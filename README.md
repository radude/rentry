# rentry

<a href="https://rentry.co/"><img width="110" height="110" src="https://rentry.co/static/logo-border-fit.png" align="right" alt="rentry.co markdown paste repository"></a>

[Rentry.co](https://rentry.co) is a markdown-powered paste/publishing service with preview, custom urls and editing.

This repo holds the official Python clients for the rentry API. `rentry.py` is a command-line tool in a single file with no dependencies. `rentry_client` is an installable library. `examples/` has one runnable script per API use case. If you'd rather write your own client, skip to the [API reference](#usage-api).

## Installation

```sh
pip install rentry
```

That gives you both the `rentry` command-line tool and the `rentry_client` library, with no dependencies.

### Single-file CLI (no pip)

The CLI also works as a single self-contained file:

```sh
wget https://raw.githubusercontent.com/radude/rentry/master/rentry.py -O ./rentry && chmod +x ./rentry
```

### From source

```sh
git clone https://github.com/radude/rentry.git
cd rentry
pip install .
```

The scripts in `examples/` additionally want `pip install -r requirements.txt`, which pulls in python-dotenv for reading a `.env` file.

### Configuration

Both the CLI and the examples default to `https://rentry.co`. Copy `.env.example` to `.env` and adjust `BASE_PROTOCOL` / `BASE_URL` if you need to point them somewhere else, such as a local dev server.

## Usage (Command-line)

```console
$ rentry --help

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
```

##### Url

Optional Url can be set (`-u, --url URL`)
It goes rentry.co/HERE. If no Url was set then random Url will be generated automatically.

##### Edit code

Optional edit code can be set (`-p, --edit-code EDIT-CODE`)
It can be used to edit the entry later. If no edit code was set then random edit code will be generated automatically. Generated edit code will be shown to you only once, so remember it or save it. You can share this code with anyone so a group of people can edit the same entry.

##### Captcha code

Optional captcha code can be set (`-c, --captcha-code CODE`), or kept in the `CAPTCHA_CODE` environment variable or `.env` file so every run uses it.
It is only needed for a page that has been temporarily locked after too many wrong edit codes. When that happens, the CLI prints a link: open it in a browser, complete the captcha and use the code it gives you. Run `rentry extend` now and then to stop the code expiring. See [Captcha codes](#captcha-codes).

## Usage (Library)

```python
from rentry_client import RentryClient

client = RentryClient()  # or RentryClient('https://my-instance.example')

page = client.new(text='hello world', metadata={'PAGE_TITLE': 'Hello'})
print(page['url'], page['edit_code'])

client.edit(page['url_short'], page['edit_code'], text='updated!')

details = client.fetch(page['url_short'], page['edit_code'])
print(details)
```

Every method hands back the parsed API response as a dict. On success, `response['status']` is `'200'`. When something goes wrong, the details are in `response['content']` and `response['errors']`.

If your client edits, fetches or deletes pages unattended, give it a [captcha code](#captcha-codes) so a locked page does not stop it:

```python
client = RentryClient(captcha_code='YOUR_CODE')  # sent with every edit, fetch and delete

result = client.edit('example', 'pw', text='updated!')
if result['status'] == '429' and 'captcha_url' in result:
    print('Locked, and the code does not work. Get a new one at', result['captcha_url'])

print(client.extend_captcha_code())  # {'status': '200', 'content': 'OK', 'expires': '2026-12-15'}
```

`edit`, `fetch` and `delete` also take `captcha_code=` to override the client's code for one request. The library never extends a code by itself, so call `extend_captcha_code()` from time to time, for example once per run.

### Examples

Each script in [`examples/`](examples/) covers one use case and runs as-is:

| Script | Use case |
|---|---|
| [`examples/new.py`](examples/new.py) | Create a page, with metadata |
| [`examples/edit.py`](examples/edit.py) | Update a page's text with its edit code |
| [`examples/edit_upsert.py`](examples/edit_upsert.py) | Change some metadata options without replacing the rest |
| [`examples/edit_modify_code.py`](examples/edit_modify_code.py) | Set a modify code, then edit with it |
| [`examples/edit_secret_metadata.py`](examples/edit_secret_metadata.py) | SECRET_* metadata: preserved by default, opt in to change it |
| [`examples/edit_change_url.py`](examples/edit_change_url.py) | Move a page to a new url and rotate its edit code |
| [`examples/fetch.py`](examples/fetch.py) | Fetch a page's full details |
| [`examples/delete.py`](examples/delete.py) | Delete a page |
| [`examples/raw.py`](examples/raw.py) | Read raw text with a rentry-auth access code |
| [`examples/captcha_code.py`](examples/captcha_code.py) | Get past a locked page with a captcha code, then extend the code |

## Usage (API)

Send a standard POST request to the below endpoints. 

NEW: The /api endpoints are CSRF-exempt, so you don't need a csrf token, cookies or a Referer header.

Starred fields are required. replace [url] with the actual URL in question (without brackets).

Example endpoint (Editing rentry.co/example): /edit/example

All fields that can be used as well as set (url, edit_code, modify_code) have new_ appended to their names when setting them.

### Metadata format

The metadata field accepts either of two syntaxes:

* Newline-separated `KEY = value` pairs, as on the website: `"PAGE_TITLE = Hello\nCONTAINER_MAX_WIDTH = 600px"`
* A JSON object: `{"OPTION_DISABLE_VIEWS": true, "CONTENT_TEXT_COLOR": ["grey", "red"]}`

There are roughly 63 options in total, covering the page itself, sharing, safety, container and content styling, and secrets. All of them are documented at [rentry.co/metadata-how](https://rentry.co/metadata-how).

### Returns

* status
* content (if status is not 200, the error will be displayed here. Otherwise, all return values below are returned contained within this field)
* errors (on validation failures: the field-level error messages)
* captcha_url (on /edit, /fetch and /delete: on every `400` while the page is gated, and on the gate's `429`; see [Captcha codes](#captcha-codes))

Responses always come back with HTTP 200, so check the `status` value inside the JSON body instead. A client should handle these: `200` success, `400` validation failed (details in `errors`), `403` access denied (raw access codes), `404` entry does not exist, `405` wrong HTTP method, `429` rate limited (back off and retry later) or captcha required, `503` database temporarily unavailable.

A `429` that carries `captcha_url` is not a rate limit: the page is gated, and retrying without a captcha code keeps failing for up to an hour. Rate-limit `429`s never carry `captcha_url`. A `400` carries `captcha_url` whenever the page is gated, whatever the error, so read `errors` for what actually failed.

### Captcha codes

Rentry pages have bruteforce protection against their edit codes and will require a captcha for all future requests, from any source, for 1 hour after the edit code was entered incorrectly 3 times. This triggers on requests to /edit, /fetch and /delete (or the web edit page) that fail with `Invalid edit code.` or `Invalid modify code.`.

Captcha codes can bypass any number of captchas where the correct edit code was provided.

* The first 2 wrong edit codes return the usual `400`. The 3rd also returns `400` and also adds `captcha_url`, and gates the page.
* The gate lasts until 1 hour after the **first** wrong edit code, not the latest. Then the counter resets and the page is open again.
* While gated, /edit, /fetch and /delete refuse any request without a working captcha code, **before** checking the edit code, so a refusal never reveals whether the edit code was right:

  ```json
  {"status": "429", "content": "Too many wrong edit codes have been submitted for this URL within the past hour. Complete the captcha at captcha_url and resend this request with the captcha_code it gives you.", "captcha_url": "https://rentry.co/edit-captcha"}
  ```

* With a working code, the request is handled normally. A right edit code succeeds and costs the code nothing. A wrong one returns `400` with `errors` and `captcha_url`, adds to the page's counter, and gives the code a strike.
* `captcha_url` on a `400` means the page is gated, not that the edit code was wrong. Every `400` from /edit, /fetch or /delete carries it while the page is gated, including other validation errors such as a bad `new_url` sent with a working code.

Anyone's wrong guesses can gate your page, so an automated client that edits pages should hold a captcha code.

**Getting one:** Open `captcha_url` (<https://rentry.co/edit-captcha>) in a browser, complete the captcha and presses *Get code*. This cannot be scripted. A code is 32 letters and digits.

**Sending it:** Apply `captcha_code` field on /edit, /fetch and /delete. It is safe to send on every request, since pages that are not gated ignore it.

**Limits:**

* One code works on every page. Strikes also count across pages: after 3 wrong edit codes sent with the code, on any pages, it expires and will need replacing.
* A code expires after 90 days without use. 
* Use means getting past a gated page with the code (whether the edit code then turns out right or wrong), or calling [/extend-captcha-code](#extend-captcha-code). **Sending the code to a page that is not gated is not use**, so a client whose pages are rarely gated should extend its code regularly. Use is recorded at most once per UTC day.

### /new

Fields:

* text *
* metadata
* url
* edit_code

Anonymous creation is rate-limited per IP, roughly 10 per minute on rentry.co and configurable per instance. A `429` status means slow down and retry later.

### /edit/[url]

You may provide a modify code to the edit_code field if one is set. Use this to give other people edit access to a page without the ability to steal it.

Fields:

* edit_code *
* text
* metadata
* update_mode
* update_secret_metadata ('true' or 'false', defaults to 'false'; see below)
* new_url
* new_edit_code
* new_modify_code (provide 'm:' to unset, this matches the website's functionality)
* captcha_code (see [Captcha codes](#captcha-codes))

##### update_mode

* **replace** (the default): the edit replaces the page, both the text and the whole metadata set. Omitting text blanks the page, and metadata options omitted from the request are removed. SECRET_* options are the exception, covered under update_secret_metadata below. For partial edits, such as only rotating a code, use upsert.
* **upsert**: the edit only changes what it provides. Metadata options in the request are added or updated, options omitted are kept, and an option sent with an empty value (`OPTION = `) is removed. Text is kept when omitted.

##### update_secret_metadata

SECRET_* metadata (SECRET_EMAIL_ADDRESS, SECRET_RAW_ACCESS_CODE, SECRET_VERIFY) is protected against accidental removal. When update_secret_metadata is 'false' or omitted, any SECRET_* option already set on the entry is preserved as-is, no matter what the request sends for it. Omitted, blanked, and changed values are all ignored for those keys.

To modify or remove a previously-set SECRET_* option, pass update_secret_metadata as the string 'true'. Adding a brand-new SECRET_* option to an entry that didn't have it never requires the flag. Alternatively, update_mode 'upsert' leaves omitted SECRETs untouched as before.

**Behavior change note:** clients that previously removed SECRET_* options by omitting them in a full-replace edit will now silently keep them until they add update_secret_metadata 'true'.

### /raw/[url]

Accepts GET or POST. Raw access is never open by default. Access codes are issued by rentry admins, so contact support@rentry.co if you need one. A page's SECRET_RAW_ACCESS_CODE metadata can only be set to a code that has already been issued, and anything else is rejected at edit time. Raw access is granted when either:

* The request carries an issued access code in the **rentry-auth header**, which grants raw access to **all** pages.
* The page itself has an issued **SECRET_RAW_ACCESS_CODE** set, which makes that page raw-readable by anyone, with no header needed.

Denials return status `403` with a message explaining which condition failed.

Returns:

* text

To fetch metadata, please use /fetch endpoint

### /fetch/[url]

Fields:

* edit_code * (a modify code is also accepted here)
* captcha_code (see [Captcha codes](#captcha-codes))

Returns:

* url
* url_case (if you set the URL with a different case structure than all lowercase, this will reflect that)
* views
* pub_date (YYYY-MM-DD T HH:MM:SS) (will not change if deleted and re-created)
* activated_date (if deleted and re-created, this is when this occured last)
* edit_date
* modify_code_set (bool)
* text
* metadata (returns as an object with key/value pairs. Each value is the entire set metadata value as a single string)
* metadata_version

### /delete/[url]

Fields:

* edit_code * (the full edit code only; a modify code cannot delete)
* captcha_code (see [Captcha codes](#captcha-codes))

### /extend-captcha-code

Records use of a captcha code without editing anything, so it does not expire, and reports when it will. POST only. A trailing slash is accepted.

Fields:

* captcha_code *

Returns:

* expires (YYYY-MM-DD, UTC: the last day the code works if nothing uses it again, which is today + 90)

| status | When |
|---|---|
| `200` | The code works, and now counts as used today |
| `404` | Missing, empty, unknown, used up (3 strikes) or expired. The response carries `captcha_url` |
| `405` | Not a POST |
| `429` | More than 10 calls in 10 minutes from one IP |
| `503` | Database briefly unavailable |
| `500` | Anything else |

```sh
curl -X POST https://rentry.co/api/extend-captcha-code -d "captcha_code=YOUR_CODE"
```

Calling it more than once a day is harmless but gains nothing.
