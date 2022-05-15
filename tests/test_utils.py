import fire
import pytest

from reddit_get import (
    RedditCli,
    get_post_sorting_option,
    get_reddit_query_function,
)


class TestUtils:
    class TestErrors:
        class TestGetPostSortingOption:
            def it_raises_a_fireerror_with_invalid_post_sorting(self):
                with pytest.raises(fire.core.FireError):
                    get_post_sorting_option('invalid')

        class TestGetRedditQueryFunction:
            def it_raises_a_fireerror_with_invalid_post_sorting(self, mock_reddit):
                with pytest.raises(fire.core.FireError):
                    cli = RedditCli('tests/.exampleconfig')
                    get_reddit_query_function(subreddit=cli.reddit.subreddit, post_sorting='invalid')
