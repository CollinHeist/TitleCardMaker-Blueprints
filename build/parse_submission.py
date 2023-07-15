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
    issue = loads(environ.get('GITHUB_CONTEXT'))
except JSONDecodeError:
    sys_exit(1)

creator = issue['user']['login']
content = issue['body']

from re import compile as re_compile
issue_regex = re_compile(
    r'^### Series Name\n+(?P<series_name>.+).*?\n+### Series Year\n+'
    r'(?P<series_year>\d+)\n+### Creator Username\n+(?P<creator>.+)\n+'
    r'### Blueprint Description\n+(?P<description>[^#]+)### Blueprint File\n+'
    r'```json\n+(?P<blueprint>[^`]+)```\n+'
    r'### Zip of Files\n+.*?\[.*\]\((?P<file_zip>.+)\).*$'
)
print(content)
if (data_match := issue_regex.match(content)):
    data = data_match.groupdict()
    print(f'{data=!r}')
else:
    print(f'{content=!r}')
    sys_exit(1)
