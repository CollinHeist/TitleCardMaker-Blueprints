"""
Python script to be called by a GitHub action.

This script parses the Github Issue JSON contained in the GITHUB_CONTEXT
environment variable. It parses this content and creates the necessary
Blueprint, and all the associated files.
"""

from argparse import SUPPRESS, ArgumentParser
from datetime import datetime
from json import dump as json_dump, dumps, loads, JSONDecodeError
from os import environ
from pathlib import Path
from re import compile as re_compile, sub as re_sub, IGNORECASE
from shutil import copy as copy_file, unpack_archive, ReadError
from sys import exit as sys_exit

from requests import get

ROOT = Path(__file__).parent.parent
BLUEPRINT_FOLDER = ROOT / 'blueprints'
TEMP_PREVIEW_FILE = ROOT / 'preview.jpg'
TEMP_FILE = ROOT / 'tmp'
TEMP_DIRECTORY = ROOT / 'unzipped'
PATH_SAFE_TRANSLATION = str.maketrans({
    '?': '!',
    '<': '',
    '>': '',
    ':':' -',
    '"': '',
    '|': '',
    '*': '-',
    '/': '+',
    '\\': '+',
})
DEFAULT_AVATAR_URL = 'https://raw.githubusercontent.com/CollinHeist/TitleCardMaker/master/.github/logo.png'

def get_blueprint_folders(series_name: str) -> tuple[str, str]:
    """
    Get the path-safe name for the given Series name.

    Args:
        series_name: Name of the Series.

    Returns:
        Path-safe name with prefix a/an/the and any illegal characters
        (e.g. '?', '|', '/', etc.) removed.
    """

    clean_name = str(series_name).translate(PATH_SAFE_TRANSLATION)
    sort_name = re_sub(r'^(a|an|the)(\s)', '', clean_name, flags=IGNORECASE)

    return sort_name[0].upper(), clean_name


# File is entrypoint
if __name__ == '__main__':
    ap = ArgumentParser()
    ap.add_argument('--discord', action='store_true')
    args = ap.parse_args()

    # If this is for a Discord message, export embeds as JSON
    if environ.get('FOR_DISCORD', 'false') == 'true':
        embeds = [
            {'title': f'New Blueprint Submission for Test (123)'},
            {'description': 'Standard card type with all the titles formatted like the logo - e.g. [title], using the Series font.'},
            {'author': {
                'name': '{creator}',
                'icon_url': environ.get('ISSUE_CREATOR_ICON_URL', DEFAULT_AVATAR_URL),
            }}, {'image': {
                'url': 'https://github.com/CollinHeist/TitleCardMaker-Blueprints/assets/17693271/b2d17252-cf5d-4d1c-83f1-752105d5c057',
            }}, {'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')},
        ]
        print(dumps(embeds))
        sys_exit(0)

    # Parse issue from environment variable
    try:
        content = loads(environ.get('ISSUE_BODY'))
        if not args.discord:
            print(f'Parsed issue JSON as:\n{content}')
    except JSONDecodeError as exc:
        print(f'Unable to parse Context as JSON')
        print(exc)
        sys_exit(1)

    # Get the issue's author and the body (the issue text itself)
    creator = environ.get('ISSUE_CREATOR', 'CollinHeist')

    # Extract the data from the issue text
    issue_regex = re_compile(
        r'^### Series Name\s+(?P<series_name>.+)\s+'
        r'### Series Year\s+(?P<series_year>\d+)\s+'
        r'### Creator Username\s+(?P<creator>.+)\s+'
        r'### Blueprint Description\s+(?P<description>[\s\S]*)\s+'
        r'### Blueprint\s+```json\s+(?P<blueprint>[\s\S]*?)```\s+'
        r'### Preview Title Card\s+.*?\[.*\]\((?P<preview_url>.+)\)\s+'
        r'### Zip of Font Files\s+(_No response_|\[.+?\]\((?P<font_zip>http[^\s\)]+)\))\s*$'
    )

    # If data cannot be extracted, exit
    if not (data_match := issue_regex.match(content)):
        print(f'Unable to parse Blueprint from Issue')
        print(f'{content=!r}')
        sys_exit(1)

    # Get each variable from the issue
    data = {'font_zip': '_No response_'} | data_match.groupdict()
    if not args.discord:
        print(f'{data=}')
    series_name = data['series_name'].strip()
    series_year = data['series_year']
    creator = (creator if '_No response_' in data['creator'] else data['creator']).strip()
    description = data['description']
    blueprint = data['blueprint']
    preview_url = data['preview_url']
    if data.get('font_zip') is None or '_No response_' in data['font_zip']:
        font_zip_url = None
    else:
        font_zip_url = data['font_zip']
    if not args.discord:
        print(f'Raw parsed data: {series_name=}\n[{series_year=}\n{creator=}\n{description=}\n{blueprint=}\n{preview_url=}\n{font_zip_url=}')

    # If this is for a Discord message, export embeds as JSON
    if args.discord:
        embeds = [{
            'title': f'New Blueprint Submission for {series_name} ({series_year})',
            'description': data['description'],
            'author': {
                'name': creator,
                'icon_url': environ.get('ISSUE_CREATOR_ICON_URL', DEFAULT_AVATAR_URL),
            }, 'image': {
                'url': preview_url,
            }, 'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        }]
        print(dumps(embeds))
        sys_exit(0)

    # Parse blueprint as JSON
    try:
        blueprint = loads(blueprint)
    except JSONDecodeError:
        print(f'Unable to parse blueprint as JSON')
        print(f'{blueprint=!r}')
        sys_exit(1)

    # Get the associated folder for this Series
    letter, folder_name = get_blueprint_folders(f'{series_name} ({series_year})')

    # Create Series folder
    series_subfolder = BLUEPRINT_FOLDER / letter / folder_name
    series_subfolder.mkdir(exist_ok=True, parents=True)

    # Find first sequential ID subfolder that does not exist
    id_ = 0
    while (blueprint_subfolder := series_subfolder / str(id_)).exists():
        id_ += 1

    # Create Blueprint ID folder
    blueprint_subfolder.mkdir(exist_ok=True, parents=True)
    print(f'Created blueprints/{letter}/{folder_name}/{id_}')

    # Generate base blueprint
    finalized_blueprint = blueprint | {
        'creator': creator,
        'description': [line.strip() for line in description.splitlines() if line.strip()],
    }

    # Download preview
    if not (response := get(preview_url, timeout=30)).ok:
        print(f'Unable to download preview file from "{preview_url}"')
        print(response.content)
        sys_exit(1)
    print(f'Downloaded preview "{preview_url}"')

    # Copy preview into blueprint folder
    TEMP_PREVIEW_FILE.write_bytes(response.content)
    copy_file(TEMP_PREVIEW_FILE, blueprint_subfolder / 'preview.jpg')
    print(f'Copied "{preview_url}" into blueprints/{letter}/{folder_name}/{id_}/preview.jpg')

    # Add preview image to blueprint
    finalized_blueprint['preview'] = 'preview.jpg'

    # Download any font zip files if provided
    if font_zip_url is not None:
        if not (response := get(font_zip_url, timeout=30)).ok:
            print(f'Unable to download zip from "{font_zip_url}"')
            print(response.content)
            sys_exit(1)
        print(f'Downloaded "{font_zip_url}"')
        zip_content = response.content
        
        # Write zip to file
        uploaded_filename = font_zip_url.rsplit('/', maxsplit=1)[-1]
        downloaded_file = ROOT / uploaded_filename
        downloaded_file.write_bytes(zip_content)

        try:
            unpack_archive(downloaded_file, TEMP_DIRECTORY)
        except (ValueError, ReadError):
            print(f'Unable to unzip provided files from "{font_zip_url}"')
            sys_exit(1)

        print(f'Unzipped {[file.name for file in TEMP_DIRECTORY.glob("*")]}')

        for file in TEMP_DIRECTORY.glob('*'):
            if file.is_dir():
                print(f'Skipping directory [zip]/{file.name}')
                continue

            copy_file(file, blueprint_subfolder / file.name)
            print(f'Copied [zip]/{file.name} into blueprints/{letter}/{folder_name}/{id_}/{file.name}')

    # Add creation time to Blueprint
    finalized_blueprint['created'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    # Write Blueprint as JSON
    blueprint_file = blueprint_subfolder / 'blueprint.json'
    with blueprint_file.open('w') as file_handle:
        json_dump(finalized_blueprint, file_handle, indent=2)
    print(f'Wrote Blueprint at blueprints/{letter}/{folder_name}/{id_}/blueprint.json')
