from __future__ import annotations

import sys
import time
from typing import TYPE_CHECKING, TypeVar

import fire
import praw
from praw.exceptions import (
    MissingRequiredAttributeException,
    RedditAPIException,
)

from .types import (
    SortingOption,
    TimeFilterOption,
)
from .utils import (
    create_post_output,
    get_post_sorting_option,
    get_reddit_query_function,
    get_response,
    get_template_keys,
    get_time_filter_option,
    load_configs,
)

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar('T')


class RedditCli:
    """Get content from reddit.

    This is intended to be a suite of command line tools that will allow
    you to get content from Reddit. Currently this is limited to getting
    the titles of posts. Use `reddit-get post --help` for more
    information.

    Authentication:
    ---------------
    This tool supports two authentication methods:

    1. Environment Variables (Recommended - OAuth2 read-only):
        export REDDIT_CLIENT_ID="your_client_id"
        export REDDIT_CLIENT_SECRET="your_client_secret"
        export REDDIT_USER_AGENT="reddit-get/1.1.0 by /u/yourusername"

    2. Configuration File (Legacy):
        Create a file at ~/.redditgetrc (or custom path) with:

        [reddit-get]
        client_id = "testid"
        client_secret = "testsecret"
        user_agent = "testuseragent"
        # Optional for read-only access:
        username = "testusername"
        password = "testpassword"

    For read-only access (this tool's primary use case), you only need
    client_id, client_secret, and user_agent. The tool will automatically
    use OAuth2 application-only authentication, which is more secure than
    storing username/password.

    To get Reddit API credentials:
    1. Visit https://www.reddit.com/prefs/apps
    2. Click "create app" or "create another app"
    3. Select "script" as the app type
    4. Use http://localhost:8080 as the redirect URI
    5. Copy the client_id and client_secret

    Args:
        config: The path on your system for your reddit credentials config file.
        Default: ~/.redditgetrc. Ignored if environment variables are set.

    """

    def __init__(self, config: str = '~/.redditgetrc') -> None:
        self.config_path, self.configs = load_configs(config)
        self.reddit = self.get_authenticated_reddit_instance()

        self.valid_header_variables: dict[str, dict[SortingOption | TimeFilterOption, str]] = {
            'sorting': {
                SortingOption.CONTROVERSIAL: 'Most Controversial',
                SortingOption.GILDED: 'Most Awarded',
                SortingOption.HOT: 'Hottest',
                SortingOption.NEW: 'Newest',
                SortingOption.RANDOM_RISING: 'Randomly Selected Rising',
                SortingOption.RISING: 'Rising',
                SortingOption.TOP: 'Top',
            },
            'time_filter': {
                TimeFilterOption.HOUR: 'the Past Hour',
                TimeFilterOption.DAY: 'the Last Day',
                TimeFilterOption.WEEK: 'the Last Week',
                TimeFilterOption.MONTH: 'Last Month',
                TimeFilterOption.YEAR: 'Last Year',
                TimeFilterOption.ALL: 'All Time',
            },
        }

    def get_authenticated_reddit_instance(self) -> praw.Reddit:
        """Create authenticated Reddit instance using OAuth2.

        Supports two authentication modes:
        1. Read-only (application-only OAuth2): Requires client_id, client_secret, user_agent
        2. User authentication (legacy): Additionally requires username, password

        For read-only access (getting posts), mode 1 is recommended and more secure.

        Returns:
            Authenticated praw.Reddit instance

        Raises:
            fire.core.FireError: If required credentials are missing or invalid
        """
        try:
            reddit = praw.Reddit(**self.configs['reddit-get'])

            # Check if we have username/password (user auth) or just client credentials (read-only)
            has_user_auth = 'username' in self.configs['reddit-get'] and 'password' in self.configs[
                'reddit-get'
            ]

            if has_user_auth and not reddit.user.me():  # pragma: no cover
                msg = 'Failed to authenticate with Reddit. Check your username and password.'
                raise fire.core.FireError(msg)

            # For read-only access, PRAW automatically uses application-only OAuth2
            # No need to verify - it will fail on first API call if credentials are invalid
            return reddit
        except MissingRequiredAttributeException as e:  # pragma: no cover
            msg = (
                f'Missing required Reddit API credentials: {e}\n'
                f'Ensure client_id, client_secret, and user_agent are set via environment '
                f'variables or config file.'
            )
            raise fire.core.FireError(msg) from e

    def config_location(self):
        """Get the path of the reddit-get config.

        Returns: The path to the config file in use for reddit-get
        """
        if self.config_path:
            return self.config_path.resolve()
        raise fire.core.FireError('No config_path has been set!')

    def _execute_with_retry(self, func: Callable[[], T], max_retries: int = 3) -> T:
        """Execute a function with exponential backoff retry logic for rate limits.

        Args:
            func: Function to execute (should return an iterable)
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            Result of func()

        Raises:
            fire.core.FireError: If max retries exceeded or other API errors occur
        """
        for attempt in range(max_retries):
            try:
                return func()
            except RedditAPIException as e:
                # Check if it's a rate limit error
                if any(item.error_type == 'RATELIMIT' for item in e.items):
                    if attempt < max_retries - 1:
                        wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                        time.sleep(wait_time)
                        continue
                    msg = (
                        'Reddit API rate limit exceeded. Please wait a minute and try again. '
                        'Consider reducing the number of requests or using a higher tier API key.'
                    )
                    raise fire.core.FireError(msg) from e

                # Handle other Reddit API errors
                error_details = ', '.join(f'{item.error_type}: {item.message}' for item in e.items)
                msg = f'Reddit API error: {error_details}'
                raise fire.core.FireError(msg) from e
            except Exception as e:  # pragma: no cover
                # Handle network errors and other exceptions
                msg = f'Error communicating with Reddit: {e!s}'
                raise fire.core.FireError(msg) from e
        msg = 'Maximum retry attempts exceeded'
        raise fire.core.FireError(msg)

    def create_header(
        self, template: str, sorting: SortingOption, time: TimeFilterOption, subreddit: str,
    ) -> str:
        valid_keys = {'sorting', 'time', 'subreddit'}
        keys = get_template_keys(template)
        if keys and not keys.issubset(valid_keys):
            raise fire.core.FireError(
                f'Invalid keys passed into header template: {", ".join(keys - valid_keys)}',
            )
        format_params = {
            'sorting': self.valid_header_variables['sorting'][sorting],
            'time': self.valid_header_variables['time_filter'][time],
            'subreddit': f'r/{subreddit}',
        }
        return template.format(**format_params)

    def post(
        self,
        subreddit: str,
        post_sorting: str = 'top',
        time_filter: str = 'all',
        limit: int = 10,
        header: bool = True,
        custom_header: str = '#### The {sorting} Posts for {time} from {subreddit}',
        output_format: str = '- {title}',
    ) -> list[str]:
        r"""Get Reddit post titles optionally formatted as markdown.

        This is a handy script for someone who is looking to get reddit
        post titles returned in a markdown format. For example, I use
        this to get the daily or weekly news, a daily quote, and some
        shower thoughts formatted as markdown from Reddit for my
        Obsidian daily tracker.

        Args:
            subreddit: Which subreddit to get posts from
            post_sorting: How to sort the posts, choose from
            'controversial', 'gilded', 'hot', 'new', 'random_rising',
            'rising', or 'top'
            time_filter: For 'controversial' or 'top' post sorting,
            choose the date range between 'hour', 'day', 'week',
            'month', 'year', or 'all'
            limit: Limit of the number of posts to get, default 10,
            limit 25
            header: Whether or not to include a header in the result.
            Default is true, use --noheader if you do not want a header.
            custom_header: Template to use for a custom header for the
            response. You can use one of 3 special keywords: 'sorting',
            'time', and 'subreddit' which should be wrapped in curly
            braces. For example, you could pass something like this:

                "--> Here are the {sorting} posts from {subreddit} for {time} <--"

            and the header would be this if you are using 'hot' for post
            sorting and 'week' for time_filter and showerthoughts for
            the subreddit:

                "--> Here Are the Hottest Posts From R/Showerthoughts for Last Week <--"

            (Note the title casing).
            output_format: The template for the output of each post. As
            with custom_header, wrap any items you want to include in
            curly braces. You can include any items from the [Praw
            Subreddit Model](http://lira.no-ip.org:8080/doc/praw-doc/html/code_overview/models/subreddit
            .html#subreddit). Hint: You can include emojis and things
            like newlines ("\n"), tabs("\t"), and anything else. Example

                "Title - {title} 🤪\nText - {selftext}\n👍🏻"

            This might have some output like this:

                Title - What do sprinters eat before a race? 🤪
                Text - Nothing, they fast
                 👍

        Returns:
            The number of post titles from the specified subreddit
            formatted as specified

        """
        if not 0 < limit <= 25:
            raise fire.core.FireError('You may only get between 1 and 25 submissions')

        sorting = get_post_sorting_option(post_sorting)

        try:
            # Get subreddit and query function
            subreddit_obj = self.reddit.subreddit(subreddit)
            query_fn = get_reddit_query_function(subreddit_obj, time_filter, sorting)

            # Execute query with retry logic for rate limits
            posts = self._execute_with_retry(lambda: list(query_fn(limit=limit)))

            return get_response(
                self.create_header(
                    template=custom_header,
                    sorting=sorting,
                    time=get_time_filter_option(time_filter),
                    subreddit=subreddit,
                ),
                create_post_output(output_format, iter(posts)),
            )
        except RedditAPIException as e:
            # Handle specific Reddit API errors (e.g., subreddit not found, private subreddit)
            if any(item.error_type in ('SUBREDDIT_NOEXIST', 'SUBREDDIT_NOTALLOWED') for item in e.items):
                msg = f"Subreddit 'r/{subreddit}' does not exist or is private/restricted"
                raise fire.core.FireError(msg) from e
            # Re-raise for _execute_with_retry to handle
            raise


def main() -> None:  # pragma: no cover
    try:
        fire.Fire(RedditCli)
    except fire.core.FireError:
        sys.exit(255)
