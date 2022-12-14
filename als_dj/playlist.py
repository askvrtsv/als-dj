from urllib.parse import quote

from als_dj.lib import DjAirtable


def _generate_track_id(dj_id: int) -> int:
    return dj_id + 100_000


def generate_track_ids(djs: list[DjAirtable]) -> list[str]:
    result = []
    for dj in djs:
        track_id = _generate_track_id(dj.id)
        result.append(f"<dict><key>Track ID</key><integer>{track_id}</integer></dict>")
    return result


def generate_tracks(djs: list[DjAirtable]) -> list[str]:
    result = []
    for dj in djs:
        track_id = _generate_track_id(dj.id)
        result.append(f"""\
            <key>{track_id}</key>
            <dict>
                <key>Track ID</key><integer>{track_id}</integer>
                <key>Name</key><string>{dj.name} — {dj.date.strftime('%d.%m.%Y')}</string>
                <key>Album</key><string>Диджеи в Студии Лебедева</string>
                <key>Genre</key><string>{_tags_as_string(dj.tags)}</string>
                <key>Kind</key><string>MPEG audio stream</string>
                <key>Track Number</key><integer>{dj.id}</integer>
                <key>Rating</key><integer>{dj.rating * 20}</integer>
                <key>Album Rating</key><integer>{dj.rating * 20}</integer>
                <key>Album Rating Computed</key><true/>
                <key>Track Type</key><string>URL</string>
                <key>Location</key><string>{quote(dj.set_url or '', safe=':/')}</string>
            </dict>"""
        )
    return result
        

def _tags_as_string(tags: list) -> str:
    sorted_tags = sorted(tags)
    if len(tags) <= 1:
        result = ''.join(sorted_tags)
    else:
        result = ', '.join(sorted_tags[:-1]) + ' и ' + sorted_tags[-1]
    result = result.capitalize()
    return result