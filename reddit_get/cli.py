import sys
from typing import (
    Dict,
    List,
    Union,
)

import fire
import praw
from praw.exceptions import MissingRequiredAttributeException

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
        self.config_path, self.configs = load_configs(config)
        self.reddit = self.get_authenticated_reddit_instance()

        self.valid_header_variables: Dict[str, Dict[Union[SortingOption, TimeFilterOption], str]] = {
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

    def get_authenticated_reddit_instance(self):
        try:
            reddit = praw.Reddit(**self.configs['reddit-get'])
            if not reddit.user.me():
                raise fire.core.FireError(  # pragma: no cover
                    'Failed to authenticate with Reddit. Did you remember your username and password?'
                )
            return reddit
        except MissingRequiredAttributeException as e:  # pragma: no cover
            fire.core.FireError(e)

    def config_location(self):
        """Get the path of the reddit-get config.

        Returns: The path to the config file in use for reddit-get
        """
        if self.config_path:
            return self.config_path.resolve()
        else:
            raise fire.core.FireError(f'No config_path has been set!')

    def create_header(
        self, template: str, sorting: SortingOption, time: TimeFilterOption, subreddit: str
    ) -> str:
        valid_keys = {'sorting', 'time', 'subreddit'}
        keys = get_template_keys(template)
        if keys and not keys.issubset(valid_keys):
            raise fire.core.FireError(
                f'Invalid keys passed into header template: {", ".join(keys - valid_keys)}'
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
        if not 0 < limit <= 25:
            raise fire.core.FireError('You may only get between 1 and 25 submissions')
        sorting = get_post_sorting_option(post_sorting)
        query_fn = get_reddit_query_function(self.reddit.subreddit(subreddit), time_filter, sorting)
        return get_response(
            self.create_header(
                template=custom_header,
                sorting=sorting,
                time=get_time_filter_option(time_filter),
                subreddit=subreddit,
            ),
            create_post_output(output_format, query_fn(limit=limit)),
        )


def main():  # pragma: no cover
    try:
        fire.Fire(RedditCli)
    except fire.core.FireError as e:
        print(e, file=sys.stderr)
        sys.exit(255)
