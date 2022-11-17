import logging

from lib import (
    fetch_djs_from_website,
    find_dj_in_airtable,
    get_djs_table,
    insert_dj,
    is_dj_changed,
    setup_logging,
    update_dj,
)

logger = logging.getLogger(__name__)


def main() -> None:
    setup_logging()

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


if __name__ == '__main__':
    main()
