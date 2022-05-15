import functools
from pathlib import Path
from string import Formatter
from typing import (
    Iterator,
    List,
    Optional,
    Set,
)

import fire
import toml
from praw.models import (
    Submission,
    Subreddit,
)

from .types import (
    CallMap,
    PrawQuery,
    SortingOption,
    TimeFilterOption,
)


def load_configs(config):
    config_path: Path = Path(config).expanduser()
    try:
        configs = toml.load(config_path)
    except (FileNotFoundError, toml.TomlDecodeError):
        raise fire.core.FireError(f'No valid TOML config found at {config_path}')
    return config_path, configs


def get_reddit_query_function(
    subreddit: Subreddit, time_filter: str = 'all', post_sorting: SortingOption = SortingOption.TOP
) -> PrawQuery:
    call_map: CallMap = {
        SortingOption.CONTROVERSIAL: functools.partial(subreddit.controversial, time_filter=time_filter),
        SortingOption.GILDED: subreddit.gilded,
        SortingOption.HOT: subreddit.hot,
        SortingOption.NEW: subreddit.new,
        SortingOption.RANDOM_RISING: subreddit.random_rising,
        SortingOption.RISING: subreddit.rising,
        SortingOption.TOP: functools.partial(subreddit.top, time_filter=time_filter),
    }
    try:
        return call_map[post_sorting]
    except KeyError:
        raise fire.core.FireError(f'Invalid sorting option: {post_sorting}')


def get_response(header: str, posts: List[str]) -> List[str]:
    response_header = [header] if header else []
    return response_header + posts


def get_time_filter_option(time_filter):
    try:
        time_filter = TimeFilterOption(time_filter)
    except ValueError:
        raise fire.core.FireError(f'{time_filter} is not a valid time filter option')
    return time_filter


def get_post_sorting_option(post_sorting: str) -> SortingOption:
    try:
        return SortingOption(post_sorting)
    except ValueError:
        raise fire.core.FireError(f'{post_sorting} is not a valid sorting option.')


def get_template_keys(template: str) -> Optional[Set[str]]:
    template_vars = {tup[1] for tup in Formatter().parse(template) if tup[1] and isinstance(tup[1], str)}
    return template_vars or None


def create_post_output(template: str, posts: Iterator[Submission]) -> List[str]:
    template_vars = get_template_keys(template)
    if not template_vars:
        raise fire.core.FireError('Your post output template did not have any items to be printed')
    results = []
    for post in posts:
        try:
            format_params = {key: getattr(post, key) for key in template_vars}
            results.append(template.format(**format_params))
        except AttributeError as e:
            raise fire.core.FireError(e)
    return results
