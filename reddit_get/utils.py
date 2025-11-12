from __future__ import annotations

import functools
import os
from pathlib import Path
from string import Formatter
from typing import TYPE_CHECKING

import fire
import toml

from .types import (
    CallMap,
    PrawQuery,
    SortingOption,
    TimeFilterOption,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from praw.models import (
        Submission,
        Subreddit,
    )


def load_configs(config: str) -> tuple[Path, dict[str, dict[str, str]]]:
    """Load Reddit credentials from environment variables or config file.

    Priority order:
    1. Environment variables (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT)
    2. Config file at specified path

    For read-only access (this tool's use case), only client_id, client_secret,
    and user_agent are required. Username and password are optional legacy config.

    Args:
        config: Path to TOML config file

    Returns:
        Tuple of (config_path, credentials_dict)

    Raises:
        fire.core.FireError: If neither environment variables nor valid config file found
    """
    config_path: Path = Path(config).expanduser()

    # Try environment variables first
    env_credentials = {
        'client_id': os.getenv('REDDIT_CLIENT_ID'),
        'client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
        'user_agent': os.getenv('REDDIT_USER_AGENT', 'reddit-get/1.1.0'),
    }

    if all(env_credentials.values()):
        # All required env vars are set, use OAuth2 application-only flow
        return config_path, {'reddit-get': env_credentials}

    # Fall back to config file
    try:
        configs = toml.load(config_path)
        # Ensure required keys are present
        required_keys = {'client_id', 'client_secret', 'user_agent'}
        if 'reddit-get' not in configs:
            msg = f'Config file {config_path} missing [reddit-get] section'
            raise fire.core.FireError(msg)
        if not required_keys.issubset(configs['reddit-get'].keys()):
            missing = required_keys - set(configs['reddit-get'].keys())
            msg = f'Config file {config_path} missing required keys: {", ".join(missing)}'
            raise fire.core.FireError(msg)
        return config_path, configs
    except FileNotFoundError as e:
        msg = (
            f'No valid TOML config found at {config_path} and required environment variables not set. '
            f'Either create a config file or set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, and '
            f'REDDIT_USER_AGENT environment variables.'
        )
        raise fire.core.FireError(msg) from e
    except toml.TomlDecodeError as e:
        msg = f'Invalid TOML syntax in config file {config_path}'
        raise fire.core.FireError(msg) from e


def get_reddit_query_function(
    subreddit: Subreddit, time_filter: str = 'all', post_sorting: SortingOption = SortingOption.TOP,
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


def get_response(header: str, posts: list[str]) -> list[str]:
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


def get_template_keys(template: str) -> set[str] | None:
    template_vars = {tup[1] for tup in Formatter().parse(template) if tup[1] and isinstance(tup[1], str)}
    return template_vars or None


def create_post_output(template: str, posts: Iterator[Submission]) -> list[str]:
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
