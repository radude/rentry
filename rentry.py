#!/usr/bin/env python3

"""A command-line client for rentry.co paste service.

This module provides a simple interface to create, edit, and retrieve entries
from rentry.co. It supports both command-line usage and programmatic access.
"""

from __future__ import annotations

import getopt
import http.cookiejar
import logging
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from enum import Enum, auto
from http.cookies import SimpleCookie
from json import loads as json_loads
from os import environ
from typing import Any, Dict, List, Mapping, Optional, Tuple

from dotenv import load_dotenv, dotenv_values

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
ENV: Mapping[str, Optional[str]] = dotenv_values()

# Constants
BASE_URL = f"{ENV['BASE_PROTOCOL']}{ENV['BASE_URL']}"
HEADERS = {"Referer": BASE_URL}
SUCCESS_STATUS = "200"


class Command(Enum):
    """Available commands for the CLI."""

    NEW = auto()
    EDIT = auto()
    RAW = auto()


@dataclass
class Entry:
    """Represents a rentry entry."""

    url: str
    edit_code: str
    text: str


class RentryError(Exception):
    """Base exception for rentry-related errors."""

    pass


class ValidationError(RentryError):
    """Raised when input validation fails."""

    pass


class ApiError(RentryError):
    """Raised when the API request fails."""

    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.errors = errors or []


class UrllibClient:
    """Simple HTTP Session Client that maintains cookies between requests.

    This class provides a wrapper around urllib.request that maintains cookies
    between requests and provides a simpler interface for making HTTP requests.

    Attributes:
        cookie_jar: A CookieJar instance that stores cookies between requests.
        opener: An OpenerDirector instance that handles HTTP requests.
    """

    def __init__(self) -> None:
        """Initialize the client with a new cookie jar and request opener."""
        self.cookie_jar: http.cookiejar.CookieJar = http.cookiejar.CookieJar()
        self.opener: urllib.request.OpenerDirector = (
            urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(self.cookie_jar)
            )
        )
        urllib.request.install_opener(self.opener)

    def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Any:
        """Make a GET request to the specified URL.

        Args:
            url: The URL to send the GET request to.
            headers: Optional dictionary of HTTP headers.

        Returns:
            The response object with status_code and data attributes.
        """
        headers = headers or {}
        request = urllib.request.Request(url, headers=headers)
        return self._request(request)

    def post(
        self,
        url: str,
        data: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make a POST request to the specified URL.

        Args:
            url: The URL to send the POST request to.
            data: Optional dictionary of form data to send.
            headers: Optional dictionary of HTTP headers.

        Returns:
            The response object with status_code and data attributes.
        """
        headers = headers or {}
        data = data or {}
        postdata = urllib.parse.urlencode(data).encode()
        request = urllib.request.Request(url, postdata, headers)
        return self._request(request)

    def _request(self, request: urllib.request.Request) -> Any:
        """Make an HTTP request and return the response.

        Args:
            request: The Request object to send.

        Returns:
            The response object with status_code and data attributes.
        """
        response = self.opener.open(request)
        response.status_code = response.getcode()
        response.data = response.read().decode("utf-8")
        return response


class RentryClient:
    """Client for interacting with the rentry.co API."""

    def __init__(self) -> None:
        """Initialize the client with a new HTTP client."""
        self.client = UrllibClient()

    def _get_csrf_token(self) -> str:
        """Get a CSRF token from the server.

        Returns:
            The CSRF token.

        Raises:
            ApiError: If the token cannot be retrieved.
        """
        try:
            cookie = SimpleCookie()
            cookie.load(
                vars(self.client.get(BASE_URL))["headers"]["Set-Cookie"]
            )
            return cookie["csrftoken"].value
        except (KeyError, AttributeError) as e:
            raise ApiError(f"Failed to get CSRF token: {e}")

    def get_raw(self, url: str) -> str:
        """Get the raw markdown text of an existing entry.

        Args:
            url: The URL of the entry to retrieve.

        Returns:
            The raw markdown text.

        Raises:
            ValidationError: If the URL is invalid.
            ApiError: If the request fails.
        """
        if not url:
            raise ValidationError("URL is required")

        endpoint = f"{BASE_URL}/api/raw/{url}"
        logger.info("Retrieving raw content from: %s", endpoint)

        response = json_loads(self.client.get(endpoint).data)
        if response["status"] != SUCCESS_STATUS:
            raise ApiError(f"Failed to get raw content: {response['content']}")

        return response["content"]

    def create_entry(self, entry: Entry) -> Entry:
        """Create a new entry.

        Args:
            entry: The entry to create.

        Returns:
            The created entry with updated URL and edit code.

        Raises:
            ValidationError: If the entry data is invalid.
            ApiError: If the request fails.
        """
        if not entry.text:
            raise ValidationError("Text is required")

        csrftoken = self._get_csrf_token()
        payload = {
            "csrfmiddlewaretoken": csrftoken,
            "url": entry.url,
            "edit_code": entry.edit_code,
            "text": entry.text,
        }

        response = json_loads(
            self.client.post(
                f"{BASE_URL}/api/new",
                payload,
                headers=HEADERS,
            ).data
        )

        if response["status"] != SUCCESS_STATUS:
            errors = response.get("errors", "").split(".")
            raise ApiError(
                f"Failed to create entry: {response['content']}",
                [e for e in errors if e],
            )

        return Entry(
            url=response["url"],
            edit_code=response["edit_code"],
            text=entry.text,
        )

    def edit_entry(self, entry: Entry) -> None:
        """Edit an existing entry.

        Args:
            entry: The entry to edit.

        Raises:
            ValidationError: If the entry data is invalid.
            ApiError: If the request fails.
        """
        if not entry.url:
            raise ValidationError("URL is required")
        if not entry.edit_code:
            raise ValidationError("Edit code is required")
        if not entry.text:
            raise ValidationError("Text is required")

        csrftoken = self._get_csrf_token()
        payload = {
            "csrfmiddlewaretoken": csrftoken,
            "edit_code": entry.edit_code,
            "text": entry.text,
        }

        response = json_loads(
            self.client.post(
                f"{BASE_URL}/api/edit/{entry.url}",
                payload,
                headers=HEADERS,
            ).data
        )

        if response["status"] != SUCCESS_STATUS:
            errors = response.get("errors", "").split(".")
            raise ApiError(
                f"Failed to edit entry: {response['content']}",
                [e for e in errors if e],
            )


def parse_args() -> Tuple[Command, Entry]:
    """Parse command line arguments.

    Returns:
        A tuple of (command, entry).

    Raises:
        ValidationError: If the arguments are invalid.
    """
    try:
        environ.pop("POSIXLY_CORRECT", None)
        opts, args = getopt.gnu_getopt(
            sys.argv[1:], "hu:p:", ["help", "url=", "edit-code="]
        )
    except getopt.GetoptError as e:
        raise ValidationError(f"Invalid command line arguments: {e}")

    command_str = (args[0:1] or [None])[0]
    if not command_str:
        raise ValidationError("No command specified")

    try:
        command = Command[command_str.upper()]
    except KeyError:
        raise ValidationError(f"Invalid command: {command_str}")

    url = ""
    edit_code = ""
    for o, a in opts:
        if o in ("-u", "--url"):
            url = urllib.parse.urlparse(a).path.strip("/")
        elif o in ("-p", "--edit-code"):
            edit_code = a

    text = (args[1:2] or [None])[0]
    if not text and command != Command.RAW:
        text = sys.stdin.read().strip()
        if not text:
            raise ValidationError("No text provided")

    return command, Entry(url=url, edit_code=edit_code, text=text or "")


def usage() -> None:
    """Print usage information for the command-line interface."""
    print("""
Usage: rentry {new | edit | raw} {-h | --help} {-u | --url} {-p | --edit-code} text

Commands:
  new   create a new entry
  edit  edit an existing entry
  raw   get raw markdown text of an existing entry

Options:
  -h, --help                 show this help message and exit
  -u, --url URL              url for the entry, random if not specified
  -p, --edit-code EDIT-CODE  edit code for the entry, random if not specified

Examples:
  rentry new 'markdown text'               # new entry with random url and edit code
  rentry new -p pw -u example 'text'       # with custom edit code and url
  rentry edit -p pw -u example 'text'      # edit the example entry
  cat FILE | rentry new                    # read from FILE and paste it to rentry
  cat FILE | rentry edit -p pw -u example  # read from FILE and edit the example entry
  rentry raw -u example                    # get raw markdown text
  rentry raw -u https://rentry.co/example  # -u accepts absolute and relative urls
    """)


def main() -> None:
    """Main entry point for the command-line interface."""
    try:
        if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
            usage()
            sys.exit(0)

        command, entry = parse_args()
        client = RentryClient()

        if command == Command.NEW:
            result = client.create_entry(entry)
            print(
                "Url:        {}\nEdit code:  {}".format(
                    result.url, result.edit_code
                )
            )
        elif command == Command.EDIT:
            client.edit_entry(entry)
            print("Ok")
        elif command == Command.RAW:
            content = client.get_raw(entry.url)
            print(content)

    except ValidationError as e:
        logger.error(str(e))
        sys.exit(1)
    except ApiError as e:
        logger.error(str(e))
        for error in e.errors:
            logger.error(error)
        sys.exit(1)
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
