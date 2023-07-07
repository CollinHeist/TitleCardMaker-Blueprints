from argparse import ArgumentParser
from pathlib import Path

from re import sub as re_sub, IGNORECASE

BLUEPRINT_FOLDER = Path(__file__).parent / 'blueprints'

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
    # Parse argument
    ap = ArgumentParser()
    ap.add_argument('series', type=str)
    args = ap.parse_args()

    # Create all subfolders
    letter, path_name = get_blueprint_folders(args.series)
    folder = BLUEPRINT_FOLDER / letter / path_name
    folder.mkdir(exist_ok=True, parents=True)
    print(f'Created "blueprints/{letter}/{path_name}"')
