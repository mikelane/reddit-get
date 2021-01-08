import functools
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Iterator

import fire
import praw
import toml
from praw.exceptions import MissingRequiredAttributeException
from praw.models.reddit.subreddit import Subreddit


class SortingOption(Enum):
    CONTROVERSIAL = 'controversial'
    GILDED = 'gilded'
    HOT = 'hot'
    NEW = 'new'
    RANDOM_RISING = 'random_rising'
    RISING = 'rising'
    TOP = 'top'


class TimeFilterOption(Enum):
    ALL = 'all'
    DAY = 'day'
    HOUR = 'hour'
    MONTH = 'month'
    WEEK = 'week'
    YEAR = 'year'


def _wrap_title(title: str, markdown: bool) -> str:
    return title if not markdown else f'- *{title}*'


class RedditCli:
    def __init__(self, config: str = '~/.redditgetrc'):
        self.config_path: Path = Path(config).expanduser()
        try:
            self.configs = toml.load(self.config_path)
        except (FileNotFoundError, toml.TomlDecodeError):
            raise fire.core.FireError(f'No valid TOML config found at {self.config_path}')
        try:
            self.reddit = praw.Reddit(**self.configs['reddit-get'])
        except MissingRequiredAttributeException as e:
            fire.core.FireError(e)
        if not self.reddit.user.me():
            raise fire.core.FireError(
                'Failed to authenticate with Reddit. Did you remember your username and password?'
            )
        self.valid_subreddit_sorting_values = set(
            item._value_ for item in SortingOption._member_map_.values()
        )
        self.valid_subreddit_time_filter_values = set(
            item._value_ for item in TimeFilterOption._member_map_.values()
        )

    def config_location(self):
        if self.config_path:
            return self.config_path.resolve()
        else:
            raise fire.core.FireError(f'No config_path has been set!')

    def post(
        self,
        subreddit: str,
        post_sorting: str = 'top',
        time_filter: str = 'all',
        limit: int = 10,
        header: bool = True,
        markdown: bool = True,
    ):
        if post_sorting not in self.valid_subreddit_sorting_values:
            raise fire.core.FireError(f'{post_sorting} is not a valid sorting option.')
        if time_filter not in self.valid_subreddit_time_filter_values:
            raise fire.core.FireError(f'{time_filter} is not a valid time filter option')
        if not 0 < limit <= 25:
            raise fire.core.FireError('You may only get between 1 and 25 submissions')

        subreddit: Subreddit = self.reddit.subreddit(subreddit)

        call_map: Dict[SortingOption, Callable[[...], Iterator[Any]]] = {
            SortingOption.CONTROVERSIAL: functools.partial(subreddit.controversial, time_filter=time_filter),
            SortingOption.GILDED: subreddit.gilded,
            SortingOption.HOT: subreddit.hot,
            SortingOption.NEW: subreddit.new,
            SortingOption.RANDOM_RISING: subreddit.random_rising,
            SortingOption.RISING: subreddit.rising,
            SortingOption.TOP: functools.partial(subreddit.top, time_filter=time_filter),
        }

        response_header = (
            [f'{"#####" * markdown} *{post_sorting.title()} Posts from r/{subreddit}*'] if header else []
        )

        return response_header + [
            f'{_wrap_title(item.title, markdown)}'
            for item in call_map[SortingOption[post_sorting.upper()]](limit=limit)
        ]


def main():
    try:
        fire.Fire(RedditCli)
    except fire.core.FireError as e:
        print(e, file=sys.stderr)
        sys.exit(255)
