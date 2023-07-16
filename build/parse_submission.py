"""
Python script to be called by a GitHub action.

TODO write
"""

from json import dump as json_dump, loads, JSONDecodeError
from os import environ
from pathlib import Path
from re import sub as re_sub, IGNORECASE
from shutil import copy as copy_file
from sys import exit as sys_exit


TCM_ROOT = Path(__file__).parent.parent
BLUEPRINT_FOLDER = TCM_ROOT / 'blueprints'
TEMP_FILE = TCM_ROOT / 'tmp'
TEMP_DIRECTORY = TCM_ROOT / 'unzipped'


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


# Parse all Blueprints
# for blueprint_file in BLUEPRINT_FOLDER.glob('*/*/*/blueprint.json'):
#     # Rewrite blueprint to format it
#     with blueprint_file.open('w') as file_handle:
#         json_dump(blueprint, file_handle, indent=2)


# File is entrypoint
if __name__ == '__main__':
    # Parse issue from environment variable
    try:
        issue = loads(environ.get('GITHUB_CONTEXT'))
    except JSONDecodeError:
        print(f'Unable to parse Context as JSON')
        sys_exit(1)

    # Get the issue's author and the body (the issue text itself)
    creator = issue['user']['login']
    content = issue['body']

    # Extract the data from the issue text
    from re import compile as re_compile
    issue_regex = re_compile(
        r'^### Series Name\n+(?P<series_name>.+).*?\n+### Series Year\n+'
        r'(?P<series_year>\d+)\n+### Creator Username\n+(?P<creator>.+)\n+'
        r'### Blueprint Description\n+(?P<description>[^#]+)### Blueprint File\n+'
        r'```json\n+(?P<blueprint>[^`]+)```\n+'
        r'### Zip of Files\n+.*?\[.*\]\((?P<file_url>.+)\).*$'
    )

    # If data cannot be extracted, exit
    if not (data_match := issue_regex.match(content)):
        print(f'Unable to parse Blueprint from Issue')
        print(f'{content=!r}')
        sys_exit(1)

    # Get each variable from the issue
    data = data_match.groupdict()
    series_name = data['series_name']
    series_year = data['series_year']
    creator = creator if data['creator'] == '_No response_' else data['creator']
    description = data['description']
    blueprint = data['blueprint']
    file_url = data['file_url']

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
    from requests import get
    response = get(file_url, timeout=30)
    if not response.ok:
        print(f'Unable to download indicated files from "{file_url}"')
        print(response.content)
        sys_exit(1)
    print(f'Downloaded "{file_url}"')
    file_content = response.content

    # Write content to file
    TEMP_FILE.write_bytes(file_content)

    # Just an image
    if file_url.lower().endswith(('.jpg', '.png', '.jpeg', '.tiff', '.webp', '.gif')):
        # Copy image into blueprint folder
        filename = file_url.rsplit('/', maxsplit=1)[-1]
        copy_file(TEMP_FILE, blueprint_subfolder / filename)
        print(f'Copied "{file_url}" into blueprints/{letter}/{folder_name}/{id_}/{filename}')
    # Zip of files
    else:
        from shutil import unpack_archive
        try:
            unpack_archive(TEMP_FILE, TEMP_DIRECTORY)
        except ValueError:
            print(f'Unable to unzip provided files from "{file_url}"')
            sys_exit(1)

        for file in TEMP_DIRECTORY.glob('*'):
            copy_file(file, blueprint_subfolder / file.name)
            print(f'Copied [zip]/{file.name} into blueprints/{letter}/{folder_name}/{id_}/{file.name}')

        