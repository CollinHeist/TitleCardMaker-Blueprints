from argparse import ArgumentParser
from pathlib import Path

from re import sub as re_sub, IGNORECASE

BLUEPRINT_FOLDER = Path(__file__).parent / 'blueprints'


def get_path_name(series_name: str) -> str:
    """
    Get the path-safe name for the given Series name.

    Args:
        series_name: Name of the Series.

    Returns:
        Path-safe name with prefix a/an/the and any illegal characters
        (e.g. '?', '|', '/', etc.) removed.
    """

    return re_sub(
        r'^(a|an|the)(\s)',
        '',
        str(series_name).translate(
            str.maketrans({
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
        ),
        flags=IGNORECASE
    )


# File is entrypoint
if __name__ == '__main__':
    # Parse argument
    ap = ArgumentParser()
    ap.add_argument('series', type=str)
    args = ap.parse_args()

    # Create all subfolder
    series_name = get_path_name(args.series)
    folder = BLUEPRINT_FOLDER / series_name[0].upper() / series_name
    folder.mkdir(exist_ok=True, parents=True)

    # Log
    print(f'Created "blueprints/{series_name[0].upper()}/{series_name}"')

    # Create blueprints.json if DNE
    file = folder / 'blueprints.json'
    if not file.exists():
        file.write_text('[\n]')
        print(f'Created blank "blueprints.json"')