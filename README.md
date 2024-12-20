# rentry

<a href="https://rentry.co/"><img width="110" height="110" src="https://rentry.co/static/logo-border-fit.png" align="right" alt="rentry.co markdown paste repository"></a>

[Rentry.co](https://rentry.co) is markdown-powered paste/publishing service with preview, custom urls and editing. 

This repository contains a simple script that allows pasting and editing from command line interface. It also gives examples for accessing each endpoint programatically.
  
## Installation

##### Manually:  
```sh
wget https://raw.githubusercontent.com/radude/rentry/master/rentry -O ./rentry && chmod +x ./rentry
```



pip install -r 'requirements.txt'
cp env_example .env

## Usage (Command Interface)

```console
$ rentry --help

Usage: rentry {new | edit | raw} {-h | --help} {-u | --url} {-p | --edit-code} text

Commands:
  new     create a new entry
  edit    edit an existing entry's text
  raw     get raw markdown text of an existing entry
  delete  delete an entry
    
Options:
  -h, --help                 show this help message and exit
  -u, --url URL              url for the entry, random if not specified
  -p, --edit-code EDIT-CODE  edit code for the entry, random if not specified
  -f, --field FIELD-NAME     the field you wish to update (use on update command only)
  -v, --value VALUE          the value you wish to update (use on update command only)

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
  rentry raw -u https://rentry.co/example  # -u accepts absolute and relative urls

  rentry delete -p pw -u example          # deletes an entry
  rentry update -p pw -u example -f 'edit_code' -v 'new-pw'   # Sets the edit code to something new
  rentry update -p pw -u example -f 'url' -v 'new_url'        # Sets the url to something new
  rentry update -p pw -u example -f 'modify_code' -v 'm:1'    # Sets the modify code to something new
  rentry update -p pw -u example -f 'modify_code' -v ''       # Unsets the modify code
  
```

##### Url

Optional Url can be set (`-u, --url URL`)  
It goes rentry.co/HERE. If no Url was set then random Url will be generated automatically.

##### Edit code

Optional edit code can be set (`-p, --edit-code EDIT-CODE`)  
It can be used to edit the entry later. If no edit code was set then random edit code will be generated automatically. Generated edit code will be shown to you only once, so remember it or save it. You can share this code with anyone so a group of people can edit the same entry.

## Usage (API)

See the example scripts for a quick start.

Send a standard POST request to the below endpoints. Make sure to provide a csrf token and a request header.

Starred fields are required. replace [url] with the actual URL in question (without brackets).

Example endpoint (Editing rentry.co/example): /edit/example

All fields that can be used as well as set (url, edit_code, modify_code) have new_ appended to their names when setting them.

### Returns

* status
* error (not present if no error)
* content (all return values below are returned contained within this field)

### /new

Fields:

* csrfmiddlewaretoken *
* text *
* metadata
* url
* edit_code

### /edit/[url]

You may provide a modify code to the edit_code field if one is set. Use this to give other people edit access to a page without the ability to steal it.

Fields:

* csrfmiddlewaretoken *
* edit_code *
* text
* metadata
* update_mode
* new_url
* new_edit_code
* new_modify_code (provide 'm:' to unset, this matches the website's functionality)

### /raw/[url]

Fields:

* csrfmiddlewaretoken *
* url

Headers:

rentry-auth (contact support@rentry.co for a code to use here. This header then gives access to all posts at /raw). Or use it as a page's metadata value : SECRET_RAW_ACCESS_CODE to permit raw access without this header.

Returns:

* text

To fetch metadata, please use /fetch endpoint

### /fetch/[url]

Fields:

* csrfmiddlewaretoken *
* edit_code *

Returns:

* url
* url_case (if you set the URL with a different case structure than all lowercase, this will reflect that)
* views
* pub_date (YYYY-MM-DD T HH:MM:SS) (will not change if deleted and re-created)
* activated_date (if deleted and re-created, this is when this occured last)
* edit_date
* modify_code_set (bool)
* text
* metadata
* metadata_version

### /delete/[url]

Fields:

* csrfmiddlewaretoken *
* edit_code *
