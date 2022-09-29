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
class Client:
    BASE_URL = 'https://api.lessonly.com/api/v1'
    MAX_GET_ATTEMPTS = 7

    def __init__(self, config):
        self.api_key = config['api_key']
        self.subdomain = config['subdomain']

    def get(self, url, params=None, headers=None):
        if not url.startswith('https://'):
            url = f'{self.BASE_URL}/{url}'

        LOGGER.info(f'Lessonly  GET {url}')

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