import requests


def _raise(resp):
    resp.raise_for_status()
    return resp


def open_url(url):
    return _raise(requests.get(url))


def get_html(url):
    return open_url(url).text
