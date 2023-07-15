"""
Python script to be called by a GitHub action.

TODO write
"""

from json import dump as json_dump, load as json_load, loads, JSONDecodeError
from os import environ
from pathlib import Path
from sys import exit as sys_exit


# BLUEPRINT_FOLDER = Path(__file__).parent.parent / 'blueprints'

# Parse all Blueprints
# for blueprint_file in BLUEPRINT_FOLDER.glob('*/*/*/blueprint.json'):
#     # Read this blueprint file
#     with blueprint_file.open('r') as file_handle:
#         # Parse JSON, skip if unable to parse
#         try:
#             blueprint = json_load(file_handle)
#         except JSONDecodeError:
#             continue

#     # Rewrite blueprint to format it
#     with blueprint_file.open('w') as file_handle:
#         json_dump(blueprint, file_handle, indent=2)


# if __name__ == '__main__':
print(environ.get('GITHUB_CONTEXT'))
try:
    context = loads(environ.get('GITHUB_CONTEXT'))
except JSONDecodeError:
    sys_exit(1)

creator = context['event']['user']['login']
content = context['event']['body']

from re import compile as re_compile
issue_regex = re_compile('^### Series Name\\n\\n(?P<series_name>[^\\]+).*\\n\\n### Series Year\\n\\n(?P<series_year>\d+)\\n\\n### Creator Username\\n\\n(?P<creator>[^\\]+)\\n\\n### Blueprint Description\\n\\n(?P<description>.+)\\n\\n### Blueprint File\\n\\n```json\\n(?P<blueprint>.+)```\\n\\n\\n### Zip of Files\\n\\n\[.*\]\((?P<file_zip>.+)\).*$')

if (data_match := issue_regex.match(content)):
    data = data_match.groupdict()
    print(data)
else:
    sys_exit(1)