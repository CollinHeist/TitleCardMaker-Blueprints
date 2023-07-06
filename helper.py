from argparse import ArgumentParser
from pathlib import Path

BLUEPRINT_FOLDER = Path(__file__).parent / 'blueprints'

# File is entrypoint
if __name__ == '__main__':
    # Parse argument
    ap = ArgumentParser()
    ap.add_argument('series', type=str)
    args = ap.parse_args()

    # Create all subfolder
    folder = BLUEPRINT_FOLDER / str(args.series[0].upper()) / str(args.series)
    folder.mkdir(exist_ok=True, parents=True)

    # Log
    print(f'Created "blueprints/{args.series[0].upper()}/{args.series}"')

    # Create blueprints.json if DNE
    file = folder / 'blueprints.json'
    if not file.exists():
        file.write_text('[\n]')
        print(f'Created blank "blueprints.json"')