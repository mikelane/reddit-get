import functools
import sys
from pathlib import Path
from string import Formatter
from typing import Any, Callable, Dict, Iterator, List, Optional, Set

import fire
import praw
import toml
from praw.exceptions import MissingRequiredAttributeException
from praw.models import Submission
from praw.models.reddit.subreddit import Subreddit
from titlecase import titlecase

from reddit_get.types import SortingOption, TimeFilterOption


class RedditCli:
    """Get content from reddit.

    This is intended to be a suite of command line tools that will allow
    you to get content from Reddit. Currently this is limited to getting
    the titles of posts. Use `reddit-get post --help` for more
    information.

    Note, In order to use this tool, you must supply your reddit
    credentials and api credentials in a file in the following format:

        [reddit-get]
        client_id = "testid"
        client_secret = "testsecret"
        user_agent = "testuseragent"
        username = "testusername"
        password = "testpassword"

    Args:
        config: The path on your system for your reddit credentials.
        Required. Default $HOME/.redditgetrc
    """

    def __init__(self, config: str = '~/.redditgetrc'):
        self.config_path: Path = Path(config).expanduser()
        try:
            self.configs = toml.load(self.config_path)
        except (FileNotFoundError, toml.TomlDecodeError):
            raise fire.core.FireError(f'No valid TOML config found at {self.config_path}')
        try:
            self.reddit = praw.Reddit(**self.configs['reddit-get'])
        except MissingRequiredAttributeException as e:  # pragma: no cover
            fire.core.FireError(e)
        if not self.reddit.user.me():
            raise fire.core.FireError(  # pragma: no cover
                'Failed to authenticate with Reddit. Did you remember your username and password?'
            )
        self.valid_header_variables: Dict[str, Dict[Optional[SortingOption, TimeFilterOption], str]] = {
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

    def config_location(self):
        """Get the path of the reddit-get config.

        Returns: The path to the config file in use for reddit-get
        """
        if self.config_path:
            return self.config_path.resolve()
        else:
            raise fire.core.FireError(f'No config_path has been set!')

    def _create_header(
        self, template: str, sorting: SortingOption, time: TimeFilterOption, subreddit: str
    ) -> str:
        valid_keys = {'sorting', 'time', 'subreddit'}
        keys = self._get_template_keys(template)
        if not keys.issubset(valid_keys):
            raise fire.core.FireError(
                f'Invalid keys passed into header template: {", ".join(keys - valid_keys)}'
            )
        format_params = {
            'sorting': self.valid_header_variables['sorting'][sorting],
            'time': self.valid_header_variables['time_filter'][time],
            'subreddit': f'r/{subreddit}',
        }
        return template.format(**format_params)

    def _create_post_output(self, template: str, posts: Iterator[Submission]) -> List[str]:
        template_vars = self._get_template_keys(template)
        results = []
        for post in posts:
            try:
                format_params = {key: getattr(post, key) for key in template_vars}
                results.append(template.format(**format_params))
            except AttributeError as e:
                raise fire.core.FireError(e)
        return results

    @staticmethod
    def _get_template_keys(template: str) -> Set[str]:
        template_vars = {tup[1] for tup in Formatter().parse(template) if tup[1]}
        return template_vars

    def post(
        self,
        subreddit: str,
        post_sorting: str = 'top',
        time_filter: str = 'all',
        limit: int = 10,
        header: bool = True,
        custom_header: str = '#### The {sorting} Posts for {time} from {subreddit}',
        output_format: str = '- {title}',
    ) -> List[str]:
        """Get Reddit post titles optionally formatted as markdown.

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
        try:
            post_sorting = SortingOption(post_sorting)
        except ValueError:
            raise fire.core.FireError(f'{post_sorting} is not a valid sorting option.')
        try:
            time_filter = TimeFilterOption(time_filter)
        except ValueError:
            raise fire.core.FireError(f'{time_filter} is not a valid time filter option')
        if not 0 < limit <= 25:
            raise fire.core.FireError('You may only get between 1 and 25 submissions')

        praw_subreddit: Subreddit = self.reddit.subreddit(subreddit)

        call_map: Dict[SortingOption, Callable[[Optional[int]], Iterator[Any]]] = {
            SortingOption.CONTROVERSIAL: functools.partial(
                praw_subreddit.controversial, time_filter=time_filter
            ),
            SortingOption.GILDED: praw_subreddit.gilded,
            SortingOption.HOT: praw_subreddit.hot,
            SortingOption.NEW: praw_subreddit.new,
            SortingOption.RANDOM_RISING: praw_subreddit.random_rising,
            SortingOption.RISING: praw_subreddit.rising,
            SortingOption.TOP: functools.partial(praw_subreddit.top, time_filter=time_filter),
        }

        response_header = (
            [
                self._create_header(
                    template=custom_header, sorting=post_sorting, time=time_filter, subreddit=subreddit
                )
            ]
            if header
            else []
        )

        posts: List[str] = self._create_post_output(output_format, call_map[post_sorting](limit=limit))

        return response_header + posts


def main():  # pragma: no cover
    try:
        fire.Fire(RedditCli)
    except fire.core.FireError as e:
        print(e, file=sys.stderr)
        sys.exit(255)
