import functools

import requests


def _raise(resp):
    resp.raise_for_status()
    return resp


def open(url):
    return _raise(session().get(url))


def _mounted(session, adapter):
    """
    Mount the adapter on http/s for the session.
    """
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


@functools.lru_cache()
def session():
    retry_strategy = requests.packages.urllib3.util.retry.Retry(
        total=5,
        backoff_factor=2,
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
    return _mounted(requests.Session(), adapter)
