#!/usr/bin/env python3

import http.cookiejar
import urllib.parse
import urllib.request
from http.cookies import SimpleCookie
from json import loads as json_loads
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

## First, create
payload = {
    "csrfmiddlewaretoken": csrftoken,
    "text": "test",
    "metadata": "SECRET_EMAIL_ADDRESS = support@rentry.co",
}
result_create = json_loads(
    client.post(
        f"{env['BASE_PROTOCOL']}{env['BASE_URL']}" + "/api/new",
        payload,
        headers=_headers,
    ).data
)
print(result_create)

## Then, edit
payload = {
    "csrfmiddlewaretoken": csrftoken,
    "text": "test updated!",
    "edit_code": result_create["edit_code"],
    "new_modify_code": "m:abc",
    "update_mode": "upsert",  # This causes only these metadata options to change, rather than a full replacement. Remove if you want to replace fully.
    "metadata": "CONTAINER_PADDING = 10px \n \
CONTAINER_MAX_WIDTH = 600px  \n \
CONTAINER_INNER_FOREGROUND_COLOR = RGBA(123,123,123,0.2) \n \
CONTAINER_INNER_BACKGROUND_COLOR = transparent \n \
CONTAINER_INNER_BACKGROUND_IMAGE = https://rentry.co/static/icons/512.png",
}
result_edit = client.post(
    f"{env['BASE_PROTOCOL']}{env['BASE_URL']}"
    + f"/api/edit/{result_create['url_short']}",
    payload,
    headers=_headers,
).data
print(result_edit)

## Edit Using modify code
payload = {
    "csrfmiddlewaretoken": csrftoken,
    "text": "test updated using modify",
    "edit_code": "m:abc",
    "update_mode": "upsert",
    "metadata": "CONTENT_FONT_WEIGHT = 600 \n \
    ",
}
result_edit = client.post(
    f"{env['BASE_PROTOCOL']}{env['BASE_URL']}"
    + f"/api/edit/{result_create['url_short']}",
    payload,
    headers=_headers,
).data
print(result_edit)
