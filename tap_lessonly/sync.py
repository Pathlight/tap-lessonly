import singer
from singer import utils, metadata
from singer.catalog import Catalog, CatalogEntry
from singer.schema import Schema
from .client import Client

LOGGER = singer.get_logger()

def sync_assignments(client, stream, state):
    singer.write_schema(
        stream_name=stream.tap_stream_id,
        schema=stream.schema.to_dict(),
        key_properties=stream.key_properties,
    )

    for new_bookmark, rows in client.paging_get('assignments', page=state.get('assignments'), per_page=1000):
        singer.write_records(stream.tap_stream_id, rows)
        singer.write_state({stream.tap_stream_id: new_bookmark})


def sync_users(client, stream, state):
    singer.write_schema(
        stream_name=stream.tap_stream_id,
        schema=stream.schema.to_dict(),
        key_properties=stream.key_properties,
    )

    for new_bookmark, rows in client.paging_get('users', page=state.get('users'), per_page=1000):
        singer.write_records(stream.tap_stream_id, rows)
        singer.write_state({stream.tap_stream_id: new_bookmark})


def sync(config, state, catalog):
    """ Sync data from tap source """
    client = Client(config)

    for stream in catalog.get_selected_streams(state):
        LOGGER.info("Syncing stream:" + stream.tap_stream_id)

        if stream.tap_stream_id == "assignments":
            sync_assignments(client, stream, state)
        if stream.tap_stream_id == "users":
            sync_users(client, stream, state)
    return
