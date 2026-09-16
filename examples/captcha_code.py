#!/usr/bin/env python3
"""Get past a page's captcha gate with a captcha code, then keep the code alive.

After 3 wrong edit codes on a page within an hour, that page's edit, fetch and
delete refuse requests without a captcha code. The refusal has status '429'
and a 'captcha_url'. A person opens captcha_url in a browser, solves the
captcha and gets a code, which works on every page.

This example gates a fresh page on purpose, shows the refusal, then retries
with the code from the CAPTCHA_CODE environment variable and extends it.
"""

import os
import sys
from urllib.error import HTTPError
from dotenv import load_dotenv
from rentry_client import RentryClient

load_dotenv()
base_url = os.getenv('BASE_PROTOCOL', 'https://') + os.getenv('BASE_URL', 'rentry.co')
captcha_code = os.getenv('CAPTCHA_CODE', '')
client = RentryClient(base_url)

page = client.new(text='captcha code example')
assert page['status'] == '200', page['content']
print(page)

# 3 wrong edit codes close the gate. The 3rd response already carries captcha_url.
# These are sent without the captcha code, so they cost the code no strikes.
for _ in range(3):
    result = client.edit(page['url_short'], 'wrong-edit-code', text='never saved')
    print(result)

# The page is now gated: even the right edit code is refused without a captcha code.
# A gate refusal always has captcha_url, unlike rate-limit 429s, and retrying
# without a code keeps failing for up to an hour.
result = client.edit(page['url_short'], page['edit_code'], text='refused')
print(result)
if result['status'] == '429' and 'captcha_url' in result and not captcha_code:
    sys.exit('Open {} in a browser, then set CAPTCHA_CODE and rerun.'.format(result['captcha_url']))

# With a working code the request is handled normally. The code is sent with
# every edit, fetch and delete, and pages that are not gated ignore it.
client = RentryClient(base_url, captcha_code=captcha_code)
result = client.edit(page['url_short'], page['edit_code'], text='edited past the gate')
print(result)

# A code expires after 90 days unused, and sending it to pages that are not
# gated does not count as use. Extending records use and reports the expiry.
try:
    result = client.extend_captcha_code()
except HTTPError as e:
    # Instances without captcha codes have no extend endpoint.
    sys.exit('{} does not support captcha codes (HTTP {})'.format(base_url, e.code))
print(result)
