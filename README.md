# Presentations

This is a repository of HedgeDoc-based presentations.

## Download Script

The `download-hedgedoc-presentation.py` script downloads presentations from pad.gwdg.de for offline viewing.

### Usage

```shell
usage: download-hedgedoc-presentation.py [-h] [-i ID] [-d DIR] [-u] [-s]

Download and save HTML and resources from pad.gwdg.de

options:
  -h, --help            show this help message and exit
  -i, --id ID           The slide ID from pad.gwdg.de
  -d, --dir DIR         The directory name (will be created as subdirectory of docs/)
  -u, --update-index-only
                        Only update the docs/index.html without downloading a presentation
  -s, --single-page-only  Only download the single-page version (s/<id>) without the full presentation
```

### Requirements

- Python 3
- `requests`, `beautifulsoup4` libraries: `pip install requests beautifulsoup4` or `uv sync`

## View Presentations

See the [github page](https://cboulanger.github.io/presentations/) for the list of all presentations.
