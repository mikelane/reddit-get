import sys
from pathlib import Path

import fire
import praw
import pytest

from reddit_get import RedditCli


# noinspection PyMethodMayBeStatic
class TestRedditCli:
    def it_sets_up_the_configs(self, mock_reddit):
        cli = RedditCli('tests/.exampleconfig')
        assert cli.configs['reddit-get']['client_id'] == 'testid'
        assert cli.configs['reddit-get']['client_secret'] == 'testsecret'
        assert cli.configs['reddit-get']['username'] == 'testusername'
        assert cli.configs['reddit-get']['password'] == 'testpassword'

    def it_handles_invalid_toml_files(self):
        with pytest.raises(fire.core.FireError):
            RedditCli('tests/.invalitomlfile')

    def it_handles_missing_config_files(self):
        with pytest.raises(fire.core.FireError):
            RedditCli('tests/.filedoesnotexist')

    def it_returns_the_config_file_path_in_use(self, mock_reddit):
        cli = RedditCli('tests/.exampleconfig')
        assert cli.config_location() == Path('tests/.exampleconfig').resolve()

    def it_handles_missing_config_paths(self, mock_reddit):
        with pytest.raises(fire.core.FireError):
            cli = RedditCli('tests/.exampleconfig')
            cli.config_path = None
            cli.config_location()

    def it_rejects_invalid_post_sorting_values(self, mock_reddit):
        with pytest.raises(fire.core.FireError):
            cli = RedditCli('tests/.exampleconfig')
            cli.post(subreddit='testsubreddit', post_sorting='invalid')

    def it_rejects_invalid_time_filter_values(self, mock_reddit):
        with pytest.raises(fire.core.FireError):
            cli = RedditCli('tests/.exampleconfig')
            cli.post(subreddit='testsubreddit', time_filter='invalid')

    def it_rejects_invalid_post_limit(self, mock_reddit):
        with pytest.raises(fire.core.FireError):
            cli = RedditCli('tests/.exampleconfig')
            cli.post(subreddit='testsubreddit', limit=0)

    def it_gets_three_controversial_posts(self, mock_reddit):
        cli = RedditCli('tests/.exampleconfig')
        result = cli.post(subreddit='testsubreddit', post_sorting='controversial', limit=3)
        expected = ['##### *Controversial Posts from r/testsubreddit*'] + ['- *controversial*'] * 3
        assert result == expected

    def it_gets_three_gilded_posts(self, mock_reddit):
        cli = RedditCli('tests/.exampleconfig')
        result = cli.post(subreddit='testsubreddit', post_sorting='gilded', limit=3)
        expected = ['##### *Gilded Posts from r/testsubreddit*'] + ['- *gilded*'] * 3
        assert result == expected

    def it_gets_hot_posts(self, mock_reddit):
        cli = RedditCli('tests/.exampleconfig')
        result = cli.post(subreddit='testsubreddit', post_sorting='hot', limit=3)
        expected = ['##### *Hot Posts from r/testsubreddit*'] + ['- *hot*'] * 3
        assert result == expected

    def it_gets_new_posts(self, mock_reddit):
        cli = RedditCli('tests/.exampleconfig')
        result = cli.post(subreddit='testsubreddit', post_sorting='new', limit=3)
        expected = ['##### *New Posts from r/testsubreddit*'] + ['- *new*'] * 3
        assert result == expected

    def it_gets_random_rising_posts(self, mock_reddit):
        cli = RedditCli('tests/.exampleconfig')
        result = cli.post(subreddit='testsubreddit', post_sorting='random_rising', limit=3)
        expected = ['##### *Random_Rising Posts from r/testsubreddit*'] + ['- *random_rising*'] * 3
        assert result == expected

    def it_gets_rising_posts(self, mock_reddit):
        cli = RedditCli('tests/.exampleconfig')
        result = cli.post(subreddit='testsubreddit', post_sorting='rising', limit=3)
        expected = ['##### *Rising Posts from r/testsubreddit*'] + ['- *rising*'] * 3
        assert result == expected

    def it_gets_top_posts(self, mock_reddit):
        cli = RedditCli('tests/.exampleconfig')
        result = cli.post(subreddit='testsubreddit', post_sorting='top', limit=3)
        expected = ['##### *Top Posts from r/testsubreddit*'] + ['- *top*'] * 3
        assert result == expected
