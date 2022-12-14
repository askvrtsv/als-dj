import datetime as dt
import html
import logging
from dataclasses import dataclass
from functools import cache

import requests
from pyairtable.api.table import Table

from als_dj import settings

logger = logging.getLogger(__name__)


@dataclass
class DjWebsite:
    id: int
    date: dt.date
    name: str
    playlist: str
    tags: list[str]
    set_url: str | None
    soundcloud_url: str | None


@dataclass
class DjAirtable(DjWebsite):
    airtable_record_id: str
    rating: int = 0


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)-8s %(message)s',
    )


def fetch_djs_from_website() -> list[DjWebsite]:
    response = requests.get(
        'https://www.artlebedev.ru/dj/json/list.html',
        headers={
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
        },
        timeout=10.0,
    )
    response.raise_for_status()
    return [make_dj_from_website(data) for data in response.json()]


def make_dj_from_website(data: dict) -> DjWebsite:
    playlist = [
        (x if isinstance(x, str) else '\n'.join(x).strip())
        for x in data.get('playlist_set') or []
    ]
    playlist = '\n'.join(html.unescape(x) for x in playlist)

    return DjWebsite(
        id=int(data['id']),
        date=dt.datetime.strptime(data['date'], '%d.%m.%Y').date(),
        name=html.unescape(data['name']),
        playlist=playlist,
        tags=sorted(x.lower() for x in data['tags']),
        # fmt: off
        set_url=(
            'https://dj.artlebedev.ru/mp3/' + data['set']['url']
            if data.get('set')
            else None
        ),
        # fmt: on
        soundcloud_url=(data['soundcloud_url'] or None),
    )


def make_dj_from_airtable(record: dict) -> DjAirtable:
    record_date = record['fields'].get('Date', '1970-01-01')
    record_date = dt.date.fromisoformat(record_date)

    return DjAirtable(
        id=record['fields'].get('Id', 0),
        date=record_date,
        name=record['fields'].get('Name', ''),
        playlist=record['fields'].get('Playlist', ''),
        tags=record['fields'].get('Tags', []),
        set_url=record['fields'].get('Set'),
        soundcloud_url=record['fields'].get('SoundCloud'),
        airtable_record_id=record['id'],
        rating=record['fields'].get('Rating', 0),
    )


def get_djs_table() -> Table:
    return Table(settings.AIRTABLE_API_KEY, 'app45gGgVmSFHUmyC', 'Sets')


@cache
def fetch_djs_from_airtable(table: Table) -> list[DjAirtable]:
    return [make_dj_from_airtable(record) for record in table.all()]


def find_dj_in_airtable(dj: DjWebsite, table: Table) -> DjAirtable | None:
    stored_djs = fetch_djs_from_airtable(table)
    for stored_dj in stored_djs:
        if stored_dj.id == dj.id:
            return stored_dj
    return None


def is_dj_changed(website_dj: DjWebsite, airtable_dj: DjAirtable) -> bool:
    return (
        website_dj.name != airtable_dj.name
        or website_dj.tags != airtable_dj.tags
        or website_dj.playlist != airtable_dj.playlist
        or website_dj.set_url != airtable_dj.set_url
    )


def insert_dj(dj: DjWebsite, table: Table) -> str:
    record: dict = table.create(
        {
            'Id': dj.id,
            'Date': dj.date.isoformat(),
            'Name': dj.name,
            'Playlist': dj.playlist,
            'Tags': dj.tags,
            'Set': dj.set_url,
            'SoundCloud': dj.soundcloud_url,
        },
        typecast=True,
    )
    return record['id']


def update_dj(dj: DjWebsite, record_id: str, table: Table) -> str:
    record: dict = table.update(
        record_id,
        fields={
            'Name': dj.name,
            'Tags': dj.tags,
            'Playlist': dj.playlist,
            'Set': dj.set_url,
        },
    )  # type: ignore
    return record['id']
