import datetime
import logging

import click

from als_dj.lib import (
    fetch_djs_from_airtable,
    fetch_djs_from_website,
    find_dj_in_airtable,
    get_djs_table,
    insert_dj,
    is_dj_changed,
    setup_logging,
    update_dj,
)
from als_dj.playlist import generate_tracks, generate_track_ids

logger = logging.getLogger(__name__)


@click.group()
def cli():
    setup_logging()


@cli.command()
def fetch_djs():
    table = get_djs_table()

    website_djs = fetch_djs_from_website()
    # Skip without set
    website_djs = [dj for dj in website_djs if dj.set_url]

    for website_dj in website_djs:
        stored_dj = find_dj_in_airtable(website_dj, table)
        if not stored_dj:
            insert_dj(website_dj, table)
        if stored_dj and is_dj_changed(website_dj, stored_dj):
            update_dj(website_dj, stored_dj.airtable_record_id, table)


@cli.command()
@click.argument('xml_playlist_file', type=click.File('w'))
def generate_playlist(xml_playlist_file) -> None:
    table = get_djs_table()
    djs = [dj for dj in fetch_djs_from_airtable(table) if dj.id]
        
    track_ids = '\n'.join(generate_track_ids(djs))
    tracks = '\n'.join(generate_tracks(djs))

    xml_playlist_file.write(f"""\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Major Version</key><integer>1</integer>
    <key>Minor Version</key><integer>1</integer>
    <key>Date</key><date>{datetime.datetime.now().isoformat()}</date>
    <key>Application Version</key><string>1.3.0.138</string>
    <key>Features</key><integer>5</integer>
    <key>Show Content Ratings</key><true/>
    <key>Tracks</key>
    <dict>
{tracks}
    </dict>
    <key>Playlists</key>
    <array>
        <dict>
            <key>Name</key><string>Диджеи в Студии Лебедева</string>
            <key>Description</key><string></string>
            <key>Playlist ID</key><integer>4985</integer>
            <key>Playlist Persistent ID</key><string>6639A40A9F7B167B</string>
            <key>All Items</key><true/>
            <key>Playlist Items</key>
            <array>
{track_ids}
            </array>
        </dict>
    </array>
</dict>
</plist>"""
    )


if __name__ == '__main__':
    cli()
