#!/usr/bin/env python3

# This script is deliberately self-contained (no imports from this repo, no hard
# dependencies) so that a single wget of this file is a working install. The
# library version of this client lives in src/rentry_client/.

import getopt
import sys
import urllib.error
import urllib.parse
import urllib.request
from json import dumps as json_dumps, loads as json_loads
from os import environ

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

base_url = environ.get('BASE_PROTOCOL', 'https://') + environ.get('BASE_URL', 'rentry.co')

# The /api endpoints are CSRF-exempt: no csrf token, cookies or Referer header needed.

# Sent on edit, fetch, delete and update. Pages that are not gated ignore it.
captcha_code = environ.get('CAPTCHA_CODE', '')


class UrllibClient:
    """Simple HTTP client."""

    def get(self, url, headers={}):
        request = urllib.request.Request(url, headers=headers)
        return self._request(request)

    def post(self, url, data=None, headers={}):
        postdata = urllib.parse.urlencode(data).encode()
        request = urllib.request.Request(url, postdata, headers)
        return self._request(request)

    def _request(self, request):
        response = urllib.request.urlopen(request)
        response.status_code = response.getcode()
        response.data = response.read().decode('utf-8')
        return response


def with_captcha_code(payload):
    if captcha_code:
        payload['captcha_code'] = captcha_code
    return payload


def raw(url, auth_code=''):
    client = UrllibClient()
    headers = {'rentry-auth': auth_code} if auth_code else {}
    return json_loads(client.get(base_url + '/api/raw/{}'.format(url), headers).data)


def fetch(url, edit_code):
    client = UrllibClient()

    payload = {
        'edit_code': edit_code
    }
    return json_loads(client.post(base_url + '/api/fetch/{}'.format(url), with_captcha_code(payload)).data)


def new(url, edit_code, text):
    client = UrllibClient()

    payload = {
        'url': url,
        'edit_code': edit_code,
        'text': text
    }
    return json_loads(client.post(base_url + '/api/new', payload).data)


def edit(url, edit_code, text):
    client = UrllibClient()

    payload = {
        'edit_code': edit_code,
        'text': text
    }
    return json_loads(client.post(base_url + '/api/edit/{}'.format(url), with_captcha_code(payload)).data)


def update(url, edit_code, field, value):
    client = UrllibClient()

    # upsert mode with no text/metadata leaves the page contents untouched,
    # so this only changes the requested credential/url field.
    payload = {
        'edit_code': edit_code,
        'update_mode': 'upsert',
        'new_' + field: value
    }
    return json_loads(client.post(base_url + '/api/edit/{}'.format(url), with_captcha_code(payload)).data)


def delete(url, edit_code):
    client = UrllibClient()

    payload = {
        'edit_code': edit_code
    }
    return json_loads(client.post(base_url + '/api/delete/{}'.format(url), with_captcha_code(payload)).data)


def extend_captcha_code():
    client = UrllibClient()

    payload = {
        'captcha_code': captcha_code
    }
    return json_loads(client.post(base_url + '/api/extend-captcha-code', payload).data)


def exit_with_errors(response):
    print('error: {}'.format(response['content']))
    try:
        for i in response['errors'].split('.'):
            i and print(i)
    except:
        pass
    # A gated page adds captcha_url to every 400, whatever the error. Only point at the captcha
    # when no code was sent or the code did not work (a 429, or a 404 from extend).
    if response.get('captcha_url'):
        if response['status'] == '400' and captcha_code:
            print('\nNote: this page is locked after too many wrong edit codes, so requests to it need a working captcha code.')
        else:
            print_captcha_help(response['captcha_url'])
    sys.exit(1)


def print_captcha_help(captcha_url):
    print('\nOpen {} in a browser and complete the captcha to get a captcha code.'.format(captcha_url))
    print('Then rerun with -c CODE, or set CAPTCHA_CODE in your environment or .env file.')


def usage():
    print('''
Usage: rentry {new | edit | raw | fetch | delete | update | extend} {-h | --help} {-u | --url} {-p | --edit-code} {-f | --field} {-v | --value} {-a | --auth-code} {-c | --captcha-code} text

Commands:
  new     create a new entry
  edit    edit an existing entry's text
  raw     get raw markdown text of an existing entry
  fetch   fetch an entry's full details (text, metadata, dates) as JSON
  delete  delete an entry
  update  update an entry's edit code, url or modify code
  extend  keep a captcha code from expiring and show its expiry date

Options:
  -h, --help                 show this help message and exit
  -u, --url URL              url for the entry, random if not specified
  -p, --edit-code EDIT-CODE  edit code for the entry, random if not specified
  -f, --field FIELD-NAME     the field you wish to update (use on update command only)
  -v, --value VALUE          the value you wish to update (use on update command only)
  -a, --auth-code CODE       rentry-auth access code (use on raw command only)
  -c, --captcha-code CODE    captcha code for pages locked after wrong edit codes,
                             defaults to the CAPTCHA_CODE environment variable

Fields: (for use on update command only)
  edit_code
  url
  modify_code

Examples:
  rentry new 'markdown text'               # new entry with random url and edit code
  rentry new -p pw -u example 'text'       # with custom edit code and url
  rentry edit -p pw -u example 'text'      # edit the example entry
  cat FILE | rentry new                    # read from FILE and paste it to rentry
  cat FILE | rentry edit -p pw -u example  # read from FILE and edit the example entry
  rentry raw -u example                    # get raw markdown text
  rentry raw -u example -a CODE            # with a rentry-auth access code
  rentry raw -u https://rentry.co/example  # -u accepts absolute and relative urls
  rentry fetch -u example -p pw            # fetch full details as JSON

  rentry delete -p pw -u example          # deletes an entry
  rentry update -p pw -u example -f 'edit_code' -v 'new-pw'   # Sets the edit code to something new
  rentry update -p pw -u example -f 'url' -v 'new_url'        # Sets the url to something new
  rentry update -p pw -u example -f 'modify_code' -v 'm:1'    # Sets the modify code to something new
  rentry update -p pw -u example -f 'modify_code' -v ''       # Unsets the modify code

  rentry edit -p pw -u example -c CODE 'text'  # edit a page locked after wrong edit codes
  rentry extend -c CODE                        # keeps a captcha code from expiring
    ''')


def main():
    global captcha_code

    try:
        environ.pop('POSIXLY_CORRECT', None)
        opts, args = getopt.gnu_getopt(sys.argv[1:], "hu:p:f:v:a:c:", ["help", "url=", "edit-code=", "field=", "value=", "auth-code=", "captcha-code="])
    except getopt.GetoptError as e:
        sys.exit("error: {}".format(e))

    command, url, edit_code, field, value, auth_code, text = None, '', '', '', None, '', None

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-u", "--url"):
            url = urllib.parse.urlparse(a).path.strip('/')
        elif o in ("-p", "--edit-code"):
            edit_code = a
        elif o in ("-f", "--field"):
            field = a
        elif o in ("-v", "--value"):
            value = a
        elif o in ("-a", "--auth-code"):
            auth_code = a
        elif o in ("-c", "--captcha-code"):
            captcha_code = a

    command = (args[0:1] or [None])[0]
    command or sys.exit(usage())
    command in ['new', 'edit', 'raw', 'fetch', 'delete', 'update', 'extend'] or sys.exit('error: command must be new, edit, raw, fetch, delete, update or extend')

    text = (args[1:2] or [None])[0]
    if not text and command in ('new', 'edit'):
        text = sys.stdin.read().strip()
        text or sys.exit('error: text is required')

    if command == 'new':
        response = new(url, edit_code, text)
        if response['status'] != '200':
            exit_with_errors(response)
        print('Url:        {}\nEdit code:  {}'.format(response['url'], response['edit_code']))

    elif command == 'edit':
        url or sys.exit('error: url is required')
        edit_code or sys.exit('error: edit code is required')

        response = edit(url, edit_code, text)
        if response['status'] != '200':
            exit_with_errors(response)
        print('Ok')

    elif command == 'raw':
        url or sys.exit('error: url is required')
        response = raw(url, auth_code)
        if response['status'] != '200':
            sys.exit('error: {}'.format(response['content']))
        print(response['content'])

    elif command == 'fetch':
        url or sys.exit('error: url is required')
        edit_code or sys.exit('error: edit code is required')

        response = fetch(url, edit_code)
        if response['status'] != '200':
            exit_with_errors(response)
        print(json_dumps(response['content'], indent=2))

    elif command == 'delete':
        url or sys.exit('error: url is required')
        edit_code or sys.exit('error: edit code is required')

        response = delete(url, edit_code)
        if response['status'] != '200':
            exit_with_errors(response)
        print('Ok')

    elif command == 'update':
        url or sys.exit('error: url is required')
        edit_code or sys.exit('error: edit code is required')
        field in ('edit_code', 'url', 'modify_code') or sys.exit('error: field must be edit_code, url or modify_code')
        if value is None or (not value and field != 'modify_code'):
            sys.exit('error: value is required')
        if field == 'modify_code' and value == '':
            value = 'm:'  # server convention for unsetting the modify code

        response = update(url, edit_code, field, value)
        if response['status'] != '200':
            exit_with_errors(response)
        print('Ok')

    elif command == 'extend':
        captcha_code or sys.exit('error: captcha code is required (-c or CAPTCHA_CODE)')

        try:
            response = extend_captcha_code()
        except urllib.error.HTTPError as e:
            # Instances without the feature answer with a real HTTP 404 page.
            if e.code == 404:
                sys.exit('error: {} does not support captcha codes'.format(base_url))
            sys.exit('error: {} returned HTTP {} {}'.format(base_url, e.code, e.reason))
        except urllib.error.URLError as e:
            sys.exit('error: could not reach {}: {}'.format(base_url, e.reason))
        if response['status'] != '200':
            exit_with_errors(response)
        print('Expires:    {} (UTC)'.format(response['expires']))


if __name__ == '__main__':
    main()
