# rentry

```console

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
