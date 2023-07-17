"""
Python script to be called by a GitHub action.

This script parses the Github Issue JSON contained in the GITHUB_CONTEXT
environment variable. It parses this content and creates the necessary
Blueprint, and all the associated files.
"""

from json import dump as json_dump, loads, JSONDecodeError
from os import environ
from pathlib import Path
from re import compile as re_compile, sub as re_sub, IGNORECASE
from shutil import copy as copy_file, unpack_archive, ReadError
from sys import exit as sys_exit

from requests import get

ROOT = Path(__file__).parent.parent
BLUEPRINT_FOLDER = ROOT / 'blueprints'
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
    # Parse issue from environment variable
    try:
        issue_json = loads(environ.get('ISSUE_JSON'))
        print(f'Parsed issue JSON as:\n{issue_json}')
    except JSONDecodeError:
        print(f'Unable to parse Context as JSON')
        sys_exit(1)

    # Get the issue's author and the body (the issue text itself)
    creator = environ.get('ISSUE_CREATOR')
    # content = issue['body']

    # Extract the data from the issue text
    # issue_regex = re_compile(
    #     r'^### Series Name\s+(?P<series_name>.+)\s+'
    #     r'### Series Year\s+(?P<series_year>\d+)\s+'
    #     r'### Creator Username\s+(?P<creator>.+)\s+'
    #     r'### Blueprint Description\s+(?P<description>[\s\S]*)\s+'
    #     r'### Blueprint File\s+```json\s+(?P<blueprint>[\s\S]*?)```\s+'
    #     r'### Zip of Files\s+.*?\[.*\]\((?P<file_url>.+)\).*$'
    # )

    # # If data cannot be extracted, exit
    # if not (data_match := issue_regex.match(content)):
    #     print(f'Unable to parse Blueprint from Issue')
    #     print(f'{content=!r}')
    #     sys_exit(1)

    # Get each variable from the issue
    # data = data_match.groupdict()
    # print(f'Regex data extracted: {data=!r}')
    # series_name = data['series_name']
    # series_year = data['series_year']
    # creator = creator if '_No response_' in data['creator'] else data['creator']
    # description = data['description']
    # blueprint = data['blueprint']
    # file_url = data['file_url']

    series_name = issue_json['series_name']
    series_year = issue_json['series_year']
    creator = issue_json['creator'] if issue_json['creator'] else environ.get('ISSUE_CREATOR')
    description = issue_json['description']
    blueprint = issue_json['blueprint']
    try:
        file_url = re_compile(r'\[.+\]\((.+)\)').match(issue_json['files']).group(1)
    except:
        print(f'Cannot parse uploaded file URL from {issue_json["files"]}')
        sys_exit(1)

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

    # Download files
    response = get(file_url, timeout=30)
    if not response.ok:
        print(f'Unable to download indicated files from "{file_url}"')
        print(response.content)
        sys_exit(1)
    print(f'Downloaded "{file_url}"')
    file_content = response.content

    # Write content to file
    uploaded_filename = file_url.rsplit('/', maxsplit=1)[-1]
    downloaded_file = ROOT / uploaded_filename
    downloaded_file.write_bytes(file_content)

    # Just an image
    if uploaded_filename.lower().endswith(('.jpg', '.png', '.jpeg', '.tiff', '.webp', '.gif')):
        # Copy image into blueprint folder
        copy_file(downloaded_file, blueprint_subfolder / uploaded_filename)
        print(f'Copied "{file_url}" into blueprints/{letter}/{folder_name}/{id_}/{uploaded_filename}')
    # Zip of files
    else:
        try:
            unpack_archive(downloaded_file, TEMP_DIRECTORY)
        except (ValueError, ReadError):
            print(f'Unable to unzip provided files from "{file_url}"')
            sys_exit(1)

        print(f'Unzipped {[file.name for file in TEMP_DIRECTORY.glob("*")]}')

        for file in TEMP_DIRECTORY.glob('*'):
            if file.is_dir():
                print(f'Skipping directory [zip]/{file.name}')
                continue

            copy_file(file, blueprint_subfolder / file.name)
            print(f'Copied [zip]/{file.name} into blueprints/{letter}/{folder_name}/{id_}/{file.name}')

    # Write Blueprint as JSON
    blueprint_file = blueprint_subfolder / 'blueprint.json'
    with blueprint_file.open('w') as file_handle:
        json_dump(finalized_blueprint, file_handle, indent=2)
    print(f'Wrote Blueprint at blueprints/{letter}/{folder_name}/{id_}/blueprint.json')
