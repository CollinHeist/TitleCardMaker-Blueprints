"""
Python script to be called by a GitHub action.

This script parses the Github Issue JSON contained in the GITHUB_CONTEXT
environment variable. It parses this content and then posts a message
on the Discord Webhook describing the created Blueprint.
"""

from datetime import datetime, timedelta
from json import loads, JSONDecodeError
from os import environ
from re import compile as re_compile
from sys import exit as sys_exit

from discord_webhook import DiscordWebhook, DiscordEmbed

DEFAULT_AVATAR_URL = (
    'https://raw.githubusercontent.com/CollinHeist/TitleCardMaker/master/'
    '.github/logo.png'
)


def get_next_merge_time(time: datetime) -> datetime:
    nearest_4hr = time.replace(
        hour=time.hour // 4 * 4,
        minute=0, second=0, microsecond=0,
    )

    return nearest_4hr + timedelta(hours=4)


def format_timedelta(delta: timedelta) -> str:
    hours, seconds = divmod(delta.total_seconds(), 3600)
    minutes = int(seconds // 60)

    if int(hours) > 1:
        return f'{int(hours)} hours, and {minutes} minute{"s" if minutes > 1 else ""}'
    if int(hours) == 1:
        return f'{int(hours)} hour, and {minutes} minute{"s" if minutes > 1 else ""}'

    return f'{minutes} minute{"s" if minutes > 1 else ""}'


# File is entrypoint
if __name__ == '__main__':
    # Parse issue from environment variable
    try:
        content = loads(environ.get('ISSUE_BODY'))
        print(f'Parsed issue JSON as:\n{content}')
    except JSONDecodeError as exc:
        print(f'Unable to parse Context as JSON')
        print(exc)
        sys_exit(1)

    # Get the issue's author and the body (the issue text itself)
    creator = environ.get('ISSUE_CREATOR', 'CollinHeist')

    # Extract the data from the issue text
    issue_regex = re_compile(
        r'^### Series Name\s+(?P<series_name>.+)\s+'
        r'### Series Year\s+(?P<series_year>\d+)\s+'
        r'### Creator Username\s+(?P<creator>.+)\s+'
        r'### Blueprint Description\s+(?P<description>[\s\S]*)\s+'
        r'### Blueprint\s+```json\s+(?P<blueprint>[\s\S]*?)```\s+'
        r'### Preview Title Card\s+.*?\[.*\]\((?P<preview_url>.+)\)\s+'
        r'### Zip of Font Files\s+(_No response_|\[.+?\]\((?P<font_zip>http[^\s\)]+)\))\s*$'
    )

    # If data cannot be extracted, exit
    if not (data_match := issue_regex.match(content)):
        print(f'Unable to parse Blueprint from Issue')
        print(f'{content=!r}')
        sys_exit(1)

    # Get each variable from the issue
    data = data_match.groupdict()

    # Create Embed object for webhook
    embed = DiscordEmbed(
        title=f'New Blueprint Submission for {data["series_name"].strip()} ({data["series_year"]})',
        description=data['description'],
    )
    embed.set_author(
        name=(creator if '_No response_' in data['creator'] else data['creator']).strip(),
        icon_url=environ.get('ISSUE_CREATOR_ICON_URL', DEFAULT_AVATAR_URL),
    )
    embed.set_image(url=data['preview_url'])
    now = datetime.now()
    next_ = get_next_merge_time(now)
    embed.set_footer(f'This Blueprint will be available in {format_timedelta(next_-now)}')

    # Add embed object to webhook, execute webhook
    webhook = DiscordWebhook(
        url=environ.get('DISCORD_WEBHOOK'),
        username=environ.get('DISCORD_USERNAME', 'MakerBot'),
        avatar_url=environ.get('DISCORD_AVATAR')
    )
    webhook.add_embed(embed)
    response = webhook.execute()
