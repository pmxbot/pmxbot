import functools

import requests


def raise(resp):
    resp.raise_for_status()
    return resp


def open_url(url):
    return raise(session().get(url))


def get_html(url):
    return open_url(url).text


@functools.lru_cache()
def session():
    retry_strategy = requests.packages.urllib3.util.retry.Retry(
        total=5,
        backoff_factor=2,
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session
