"""
Python script to be called by a GitHub action.

This script reads all Series blueprints.json files and writes summary
README's within each Series subfolder.
"""

from json import load as json_load, JSONDecodeError
from pathlib import Path

README_TEMPLATE = """# TitleCardMaker Blueprints

Blueprints for importing premade Series configurations into TitleCardMaker.

---

There are currently `{blueprint_count}` Blueprints available for `{series_count}` Series, submitted by `{creator_count}` Creators.

Series with the most Blueprints:
| Series | Blueprints |
| :--- | :--- |
| {series_name0} | {series_bp_count0} |
| {series_name1} | {series_bp_count1} |
| {series_name2} | {series_bp_count2} |
| {series_name3} | {series_bp_count3} |
| {series_name4} | {series_bp_count4} |

Creators with the most Blueprint Submissions:
| Username | Blueprints |
| :---: | :--- |
| {username0} | {username_bp_count0} |
| {username1} | {username_bp_count1} |
| {username2} | {username_bp_count2} |
| {username3} | {username_bp_count3} |
| {username4} | {username_bp_count4} |
"""

# Parse Master Blueprint
with (Path(__file__).parent.parent / 'master_blueprints.json').open('r') as fh:
    # Parse JSON, skip if unable to parse
    try:
        blueprints = json_load(fh)
    except JSONDecodeError:
        exit(1)

# Get top Series
series_data: dict[str, int] = {}
for blueprint in blueprints:
    if blueprint['series_full_name'] in series_data:
        series_data[blueprint['series_full_name']] += 1
    else:
        series_data[blueprint['series_full_name']] = 1
top_series = sorted(series_data.items(), key=lambda item: item[1], reverse=True)

# Get top usernames
user_data: dict[str, int] = {}
for blueprint in blueprints:
    creators = map(str.strip, blueprint['creator'].split(','))
    for creator in creators:
        if creator in user_data:
            user_data[creator] += 1
        else:
            user_data[creator] = 1
top_users = sorted(user_data.items(), key=lambda item: item[1], reverse=True)

def get_nth_user(n: int) -> tuple[str, str]:
    try:
        return top_users[n]
    except IndexError:
        return '-', '-'

# Generate counts
data = {
    'blueprint_count': len(blueprints),
    'series_count': len(set(bp['series_full_name'] for bp in blueprints)),
    'creator_count': len(set(bp['creator'] for bp in blueprints)),
    'series_name0': top_series[0][0], 'series_bp_count0': top_series[0][1],
    'series_name1': top_series[1][0], 'series_bp_count1': top_series[1][1],
    'series_name2': top_series[2][0], 'series_bp_count2': top_series[2][1],
    'series_name3': top_series[3][0], 'series_bp_count3': top_series[3][1],
    'series_name4': top_series[4][0], 'series_bp_count4': top_series[4][1],
    'username0': get_nth_user(0)[0], 'username_bp_count0': get_nth_user(0)[1],
    'username1': get_nth_user(1)[0], 'username_bp_count1': get_nth_user(1)[1],
    'username2': get_nth_user(2)[0], 'username_bp_count2': get_nth_user(2)[1],
    'username3': get_nth_user(3)[0], 'username_bp_count3': get_nth_user(3)[1],
    'username4': get_nth_user(4)[0], 'username_bp_count4': get_nth_user(4)[1],
}

# Write README file
readme = README_TEMPLATE.format(**data)
readme_file = Path(__file__).parent.parent / 'README.md'
readme_file.write_text(readme)
