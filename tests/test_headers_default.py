"""Regression tests: HTTP helpers must not share a mutable default headers dict.

CPython's urllib.request.Request keeps a live reference to the headers dict
it is given (``self.headers = headers``), so a ``headers={}`` default is
polluted process-wide as soon as any request object is mutated (redirect
handling and auth handlers call ``add_header``). Each call must build a
fresh dict instead.
"""

import sys
import unittest

sys.path.insert(0, "src")
sys.path.insert(0, ".")

import urllib.request

import rentry as rentry_cli
from rentry_client.client import RentryClient


class AliasingRequest:
    """Mimics CPython Request's aliasing of the passed headers dict."""

    instances = []

    def __init__(self, url, data=None, headers=None, **kwargs):
        self.headers = headers if headers is not None else {}
        AliasingRequest.instances.append(self)

    def add_header(self, key, value):
        self.headers[key] = value


class HeadersDefaultTests(unittest.TestCase):
    def setUp(self):
        AliasingRequest.instances.clear()
        self._real_request = urllib.request.Request
        urllib.request.Request = AliasingRequest

    def tearDown(self):
        urllib.request.Request = self._real_request

    def test_library_get_uses_fresh_headers_dicts(self):
        client = RentryClient()
        client._request = lambda req: {}
        client._get("/api/raw/x")
        client._get("/api/raw/x")
        first, second = AliasingRequest.instances[-2:]
        self.assertIsNot(first.headers, second.headers)
        first.add_header("X-Leak", "1")  # simulate redirect/auth mutation
        self.assertNotIn("X-Leak", second.headers)

    def test_cli_get_and_post_use_fresh_headers_dicts(self):
        cli = rentry_cli.UrllibClient()
        cli._request = lambda req: req
        first_get = cli.get("http://example.invalid/a")
        second_get = cli.get("http://example.invalid/a")
        self.assertIsNot(first_get.headers, second_get.headers)
        first_post = cli.post("http://example.invalid/b", {"x": "1"})
        second_post = cli.post("http://example.invalid/b", {"x": "1"})
        self.assertIsNot(first_post.headers, second_post.headers)


if __name__ == "__main__":
    unittest.main()
