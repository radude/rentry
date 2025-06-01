#!/usr/bin/env python3

import http.cookiejar
import urllib.parse
import urllib.request
from http.cookies import SimpleCookie
import json
from dotenv import load_dotenv, dotenv_values

load_dotenv()
env = dotenv_values()

_headers = {"Referer": f"{env['BASE_PROTOCOL']}{env['BASE_URL']}"}


class UrllibClient:
    """Simple HTTP Session Client, keeps cookies."""

    def __init__(self):
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )
        urllib.request.install_opener(self.opener)

    def get(self, url, headers={}):
        request = urllib.request.Request(url, headers=headers)
        return self._request(request)

    def post(self, url, data=None, headers={}):
        postdata = urllib.parse.urlencode(data).encode()
        request = urllib.request.Request(url, postdata, headers)
        return self._request(request)

    def _request(self, request):
        response = self.opener.open(request)
        response.status_code = response.getcode()
        response.data = response.read().decode("utf-8")
        return response


client, cookie = UrllibClient(), SimpleCookie()

cookie.load(
    vars(client.get(f"{env['BASE_PROTOCOL']}{env['BASE_URL']}"))["headers"][
        "Set-Cookie"
    ]
)
csrftoken = cookie["csrftoken"].value

# Provide metadata as a newline separated string, as on the website
metadata = "OPTION_DISABLE_VIEWS = true \n \
    CONTAINER_MAX_WIDTH = 600px "

# Or, Format metadata as JSON
metadata_obj = {
    "OPTION_DISABLE_VIEWS": True,
    "CONTENT_TEXT_COLOR": ["grey", "red"],
}
metadata = json.dumps(metadata_obj)


payload = {"csrfmiddlewaretoken": csrftoken, "text": "test", "metadata": metadata}
result = json.loads(
    client.post(
        f"{env['BASE_PROTOCOL']}{env['BASE_URL']}" + "/api/new",
        payload,
        headers=_headers,
    ).data
)
print(result)
