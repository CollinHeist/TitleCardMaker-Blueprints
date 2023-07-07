from json import load as json_load, JSONDecodeError
from pathlib import Path

from re import compile as re_compile, sub as re_sub, IGNORECASE

BLUEPRINT_FOLDER = Path(__file__).parent.parent / 'blueprints'

# Non-tests

def read_blueprints(skip_null: bool = True):
    for blueprint_file in BLUEPRINT_FOLDER.glob('*/*/blueprints.json'):
        series_subfolder = blueprint_file.parent
        with blueprint_file.open('r') as file_handle:
            for blueprint_id, blueprint in enumerate(json_load(file_handle)):
                if skip_null and blueprint is None:
                    continue

                yield series_subfolder, blueprint_id, blueprint

    return None

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

# Tests

class TestFolderOrganization:
    def test_subfolder_names(self):
        for folder in BLUEPRINT_FOLDER.glob('*'):
            assert folder.name.upper() == folder.name, 'Folder Names Must Be Uppercase'

    def test_series_in_correct_subfolder(self):
        for series_folder in BLUEPRINT_FOLDER.glob('*/*'):
            letter, _ = get_blueprint_folders(series_folder)
            assert series_folder.parent.name == letter, 'Series must be placed in the correct letter subfolder'

    def test_series_folder_names(self):
        NAME_REGEX = re_compile(r'^.+\(\d{4}\)$')
        for series_folder in BLUEPRINT_FOLDER.glob('*/*'):
            assert NAME_REGEX.match(series_folder.name), 'Series Folder Names Must be Formatted as "Name (Year)"'

    def test_series_blueprint_folder_names(self):
        for folder in BLUEPRINT_FOLDER.glob('*/*/*'):
            if folder.is_file():
                continue

            assert folder.name.isdigit(), 'Series Blueprint subfolders must be named their blueprint ID'
            assert str(int(folder.name)) == folder.name, 'Series Blueprint subfolders must not be zero-padded'

    def test_series_subfolder_files(self):
        for file in BLUEPRINT_FOLDER.glob('*/*/*'):
            if file.is_dir():
                continue

            assert file.name == 'blueprints.json', 'Only "blueprints.json" is allowed at root of Series Subfolder'


class TestBlueprintJSON:
    def test_blueprint_valid_json(self):
        for file in BLUEPRINT_FOLDER.glob('*/*/blueprints.json'):
            content = None
            with file.open('r') as file_handle:
                try:
                    content = json_load(file_handle)
                except JSONDecodeError:
                    pass

            assert content is not None, 'All blueprints.json files must be valid JSON and cannot be empty'
            assert isinstance(content, list), 'All blueprint files must have a top-level list'

    def test_blueprint_json_has_required_data(self):
        for _, _, blueprint in read_blueprints():
            assert isinstance(blueprint, dict), 'Invalid blueprint JSON'
            assert 'description' in blueprint.keys(), 'All blueprints must have a "description" field'
            assert isinstance(blueprint['description'], list) and len(blueprint['description']) > 0, 'All blueprint descriptions must be a list'
            assert 'preview' in blueprint.keys(), 'All blueprints must have a "preview" field'
            assert 'creator' in blueprint.keys(), 'All blueprints must have a "creator" field'


class TestBlueprintSubfolders:
    def test_blueprint_has_subfolder(self):
        for series_subfolder, blueprint_id, _ in read_blueprints():
            assert (series_subfolder / str(blueprint_id)).exists(), 'Every blueprint must have a subfolder'

    def test_deleted_blueprints_has_no_subfolder(self):
        for series_subfolder, blueprint_id, blueprint in read_blueprints(skip_null=False):
            if blueprint is not None:
                continue

            assert not (series_subfolder / str(blueprint_id)).exists(), 'Deleted blueprints must have no subfolder'


class TestBlueprintFiles:
    def test_blueprint_identifies_all_files(self):
        for series_subfolder, blueprint_id, blueprint in read_blueprints():
            # Get list of files in the blueprint subfolder
            given_files = {file.name for file in (series_subfolder / str(blueprint_id)).glob('*')}
            # Get all files listed in any Fonts
            font_files = {
                font['file']
                for font in blueprint.get('fonts', [])
                if font.get('file', None) is not None
            }
            assert len(given_files - font_files - {blueprint['preview']}) == 0, 'Only files listed in the blueprint can be included in the blueprint folder'
            assert len((font_files | {blueprint['preview']}) - given_files) == 0, 'All files listed in the blueprint must be included in the blueprint folder'
