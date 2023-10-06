"""
Python script to be called by a GitHub action.

This script combines all blueprint files into a single master
blueprint.json file that can be parsed for purposes of browsing
blueprints.
"""

from json import dump as json_dump, load as json_load, JSONDecodeError
from pathlib import Path


BLUEPRINT_FOLDER = Path(__file__).parent.parent / 'blueprints'
MASTER_BLUEPRINT = Path(__file__).parent.parent / 'master_blueprints.json'

REPO_URL = (
    'https://github.com/CollinHeist/TitleCardMaker-Blueprints/'
    'raw/master/blueprints'
)


all_blueprints = []
for blueprint_file in BLUEPRINT_FOLDER.glob('*/*/blueprints.json'):
    series_subfolder = blueprint_file.parent
    letter_subfolder = series_subfolder.parent
    series_full_name = series_subfolder.name

    # Read this blueprint file
    with blueprint_file.open('r') as file_handle:
        # Parse JSON, skip if unable to parse
        try:
            blueprint_json = json_load(file_handle)
        except JSONDecodeError:
            continue

        # Go through all blueprints in this file
        for blueprint_id, blueprint in enumerate(blueprint_json):
            # Skip null blueprints
            if blueprint is None:
                continue

            # Add Series name and blueprint ID
            blueprint['series_full_name'] = series_full_name
            blueprint['id'] = blueprint_id

            # Update preview to be fully resolved link
            blueprint['preview'] = (
                f'{REPO_URL}/{letter_subfolder.name}/{series_subfolder.name}/'
                f'{blueprint_id}/{blueprint["preview"]}'
            )

            # Add to master list
            all_blueprints.append(blueprint)

# Write updated master list
with MASTER_BLUEPRINT.open('w') as file_handle:
    json_dump(all_blueprints, file_handle, indent=2)
