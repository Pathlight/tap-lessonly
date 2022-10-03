import datetime
import enum
import json
import logging
import os
import time
import urllib.parse

from dateutil.parser import parse as parse_datetime
import jwt
import requests
import requests.exceptions
import singer

LOGGER = singer.get_logger()


def set_query_parameters(url, **params):
    """Given a URL, set or replace a query parameter and return the
    modified URL.

    >>> set_query_parameters('http://example.com?foo=bar&biz=baz', foo='stuff', bat='boots')
    'http://example.com?foo=stuff&biz=baz&bat=boots'

    """
    scheme, netloc, path, query_string, fragment = urllib.parse.urlsplit(url)
    query_params = urllib.parse.parse_qs(query_string)

    new_query_string = ''

    for param_name, param_value in params.items():
        query_params[param_name] = [param_value]
        new_query_string = urllib.parse.urlencode(query_params, doseq=True)

    return urllib.parse.urlunsplit((scheme, netloc, path, new_query_string, fragment))


class Client:
    BASE_URL = 'https://api.lessonly.com/api/v1'
    MAX_GET_ATTEMPTS = 7

    def __init__(self, config):
        self.api_key = config['api_key']
        self.subdomain = config['subdomain']

    def get(self, url, params=None, headers=None):
        if not url.startswith('https://'):
            url = f'{self.BASE_URL}/{url}'

        LOGGER.info(f'Lessonly GET {url}')

        for num_retries in range(self.MAX_GET_ATTEMPTS):
            will_retry = num_retries < self.MAX_GET_ATTEMPTS - 1
            try:
                resp = requests.get(url, params=params, auth=(self.subdomain,self.api_key))
            # Catch the base exception from requests
            except requests.exceptions.RequestException as e:
                resp = None
                if will_retry:
                    LOGGER.info('Lessonly: unable to get response, will retry', exc_info=True)
                else:
                    raise APIQueryError({'message': str(e)}) from e
            if will_retry:
                if resp and resp.status_code >= 500:
                    LOGGER.info('Lessonly request with 5xx response, retrying', extra={
                        'url': resp.url,
                        'reason': resp.reason,
                        'code': resp.status_code
                    })
                # resp will be None if there was a `ConnectionError`
                elif resp is not None:
                    break  # No retry needed
                time.sleep(60)

        resp.raise_for_status()
        return resp.json()

    def paging_get(self, stream_name, **get_args):
        requested_urls = set()

        sequence_id = 0
        MAX_RESPONSE_SIZE = 1000

        url = stream_name
        if not url.startswith('https://'):
            url = f'{self.BASE_URL}/{url}'

        get_args = {k: v for k, v in get_args.items() if v is not None}
        url = set_query_parameters(url, **get_args)

        while url and url not in requested_urls:
            requested_urls.add(url)
            data = self.get(url)
            results = data.get(stream_name)
            total_pages = data.get('total_pages')

            LOGGER.info('Lessonly paging request', extra={
                'total_pages': total_pages,
                'total_size': data.get('per_page'),
                'page': data.get('page'),
                'url': url,
            })

            if data:
                page = data.get('page')
                yield page, results

            if total_pages is None or page + 1 > total_pages:
                break

            url = set_query_parameters(url, page=page+1)