"""
Python script to be called by a GitHub action.

This script combines all blueprint files for each Series into a single
series blueprints.json file that can be parsed when browsing Blueprints
per-Series.
"""

from json import dump as json_dump, load as json_load, JSONDecodeError
from pathlib import Path


BLUEPRINT_FOLDER = Path(__file__).parent.parent / 'blueprints'

# Parse all Blueprints for all Series
series_blueprints = {}
for blueprint_file in BLUEPRINT_FOLDER.glob('*/*/*/blueprint.json'):
    blueprint_id = int(blueprint_file.parent.name)
    series_subfolder = blueprint_file.parent.parent
    letter_subfolder = series_subfolder.parent

    # File to write all of this Series' blueprints to
    series_blueprint_file = series_subfolder / 'blueprints.json'

    # Read this blueprint file
    with blueprint_file.open('r') as file_handle:
        # Parse JSON, skip if unable to parse
        try:
            blueprint = json_load(file_handle)
        except JSONDecodeError:
            continue

        # Append Blueprint at it's ID
        if series_blueprint_file in series_blueprints:
            # Already an entry for this Series, just add to it
            series_blueprints[series_blueprint_file][blueprint_id] = blueprint
        else:
            # Add entry for Series and this Blueprint
            series_blueprints[series_blueprint_file] = {blueprint_id: blueprint}

# Create blueprints.json files for all Series
for series_blueprint_file, blueprint_map in series_blueprints.items():
    # Create sorted list of Blueprints for this Series, putting null if DNE
    blueprint_list = [
        blueprint_map.get(blueprint_id, None)
        for blueprint_id in range(max(blueprint_map.keys())+1)
    ]

    # Write list to Series blueprints.json file
    with series_blueprint_file.open('w') as file_handle:
        json_dump(blueprint_list, file_handle, indent=2)
