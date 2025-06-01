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
    "metadata": "OPTION_DISABLE_VIEWS = true",
    #'edit_code' : 'custom_edit_code',
    #'url' : 'custom_url',
}
result_create = json_loads(
    client.post(
        f"{env['BASE_PROTOCOL']}{env['BASE_URL']}" + "/api/new",
        payload,
        headers=_headers,
    ).data
)
print(result_create)

## Then, delete
payload = {
    "csrfmiddlewaretoken": csrftoken,
    "edit_code": result_create["edit_code"],
}
# result_delete = client.post(f"{env['BASE_PROTOCOL']}{env['BASE_URL']}" + f"/api/delete/{result_create['url_short']}", payload, headers=_headers).data
result_delete = client.post(
    f"{env['BASE_PROTOCOL']}{env['BASE_URL']}"
    + f"/api/delete/{result_create['url_short']}",
    payload,
    headers=_headers,
).data
print(result_delete)
