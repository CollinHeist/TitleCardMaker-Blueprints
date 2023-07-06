"""
Python script to be called by a GitHub action.

This script resizes all preview images to a size of 1920x1080.
"""
from json import load as json_load, JSONDecodeError
from pathlib import Path

from imagesize import get as get_image_size
from PIL import Image


IMAGE_SIZE = (1920, 1080)

BLUEPRINT_FOLDER = Path(__file__).parent.parent / 'blueprints'

REPO_URL = (
    'https://github.com/CollinHeist/TitleCardMaker-Blueprints/'
    'raw/master/blueprints'
)


for blueprint_file in BLUEPRINT_FOLDER.glob('*/*/blueprints.json'):
    # Read this blueprint file
    series_subfolder = blueprint_file.parent
    with blueprint_file.open('r') as file_handle:
        # Parse JSON, skip if unable to parse
        try:
            blueprint_json = json_load(file_handle)
        except JSONDecodeError:
            continue

        # Go through all Blueprints in this file
        for blueprint_id, blueprint in enumerate(blueprint_json):
            # Skip null Blueprints
            if blueprint is None:
                continue

            # Get this Blueprint's preview
            preview = series_subfolder / str(blueprint_id) /blueprint['preview']

            # Verify image is 1920x1080
            width, height = get_image_size(preview)
            if (width not in range(IMAGE_SIZE[0]-5, IMAGE_SIZE[0]+5)
                or height not in range(IMAGE_SIZE[1]-5, IMAGE_SIZE[1]+5)):
                image = Image.open(preview).resize(IMAGE_SIZE)
                image.save(preview)
                print(f'Resized "{preview}" to 1920x1080')
