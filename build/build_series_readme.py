"""
Python script to be called by a GitHub action.

This script reads all Series blueprints.json files and writes summary
README's within each Series subfolder.
"""

from json import load as json_load, JSONDecodeError
from pathlib import Path

README_TEMPLATE = """# {series_full_name}

There are `{count}` Blueprint(s) available for this Series.

| ID | Preview | Templates | Fonts | Episodes | 
| :---: | :---: | :---: | :---: | :---: |"""
# README_FOOTER = '\n\n> Note: This is an auto-generated file'

README_TABLE_ROW = '| `{blueprint_id}` | <img src="./{blueprint_id}/{preview_file}" height="150"> | {template_count} | {font_count} | {episode_count} |'

def format_count(count: int) -> str:
    return f'`{count}`' if count else '-'

# Parse all Blueprints for all Series
BLUEPRINT_FOLDER = Path(__file__).parent.parent / 'blueprints'
series_blueprints = {}
for blueprint_file in BLUEPRINT_FOLDER.glob('*/*/blueprints.json'):
    series_subfolder = blueprint_file.parent

    # Read this Series blueprint file
    with blueprint_file.open('r') as file_handle:
        # Parse JSON, skip if unable to parse
        try:
            blueprints = json_load(file_handle)
        except JSONDecodeError:
            continue

    # Generate README for this Series
    readme = README_TEMPLATE.format(
        series_full_name=series_subfolder.name,
        count=len(blueprints),
    )
    for blueprint_id, blueprint in enumerate(blueprints):
        if blueprint is None:
            continue

        readme += '\n' + README_TABLE_ROW.format(
            blueprint_id=blueprint_id,
            preview_file=blueprint['preview'],
            template_count=format_count(len(blueprint.get('templates', []))),
            font_count=format_count(len(blueprint.get('fonts', []))),
            episode_count=format_count(len(blueprint.get('episodes', []))),
        )
    # readme += README_FOOTER

    # Write README file for this Series
    readme_file = series_subfolder / 'README.md'
    readme_file.write_text(readme)
