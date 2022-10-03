import singer
from singer import utils, metadata
from singer.catalog import Catalog, CatalogEntry
from singer.schema import Schema
from .client import Client

LOGGER = singer.get_logger()

def sync(config, state, catalog):
    """ Sync data from tap source """
    client = Client(config)
    # Loop over selected streams in catalog
    for stream in catalog.get_selected_streams(state):
        LOGGER.info("Syncing stream:" + stream.tap_stream_id)

        singer.write_schema(
            stream_name=stream.tap_stream_id,
            schema=stream.schema.to_dict(),
            key_properties=stream.key_properties,
        )
        # TODO: delete and replace this inline function with your own data retrieval process:
        PAGE_START = 1
        if stream.tap_stream_id == "assignments":
            while True:
                tap_data = client.get('assignments/?page={}&per_page=1000'.format(PAGE_START))
                if not len(tap_data.get("assignments")) > 0:
                    break
                singer.write_records(stream.tap_stream_id,tap_data.get("assignments"))
                PAGE_START += 1
        if stream.tap_stream_id == "users":
            while True:
                tap_data = client.get('users?page={}&per_page=1000'.format(PAGE_START))
                if not len(tap_data.get("users")) > 0:
                    break
                singer.write_records(stream.tap_stream_id,tap_data.get("users"))
                PAGE_START += 1
    return