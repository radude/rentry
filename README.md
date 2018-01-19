# rentry

<a href="https://rentry.co/"><img width="110" height="110" src="https://rentry.co/static/logo-border-fit.png" align="right" alt="rentry.co markdown pastebin"></a>

[Rentry.co](https://rentry.co) is markdown-powered pastebin/publishing service with preview, custom urls and editing. 

This repository contains a simple script that allows pasting and editing from command line interface.  
  
  
## Installation

##### Manually:  
```sh
wget https://raw.githubusercontent.com/radude/rentry/master/rentry -O ./rentry && chmod +x ./rentry
```

##### [PyPI](https://pypi.python.org/pypi/rentry):
```sh
pip3 install rentry
```

## Usage

```console
$ rentry --help

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
  cat file | rentry new                    # read from pipe and paste it to rentry
  rentry raw -u example                    # get raw markdown text
  rentry raw -u https://rentry.co/example  # -u accepts absolute and relative urls
    
```

##### Url

Optional Url can be set. It goes rentry.co/HERE. If no Url was set then random Url will be generated automatically.

##### Edit code

Optional Edit code can be set. It can be used to edit the entry later. If no Edit code was set then random Edit code will be generated automatically. Generated Edit code will be shown to you only once, so remember it or save it.

