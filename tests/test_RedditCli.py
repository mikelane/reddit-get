import sys
from pathlib import Path

import fire
import praw
import pytest

from reddit_get import RedditCli


class MockRedditor:
    def me(self):
        return 'Mocked Redditor'


class MockSubmission:
    def __init__(self, title):
        self.title = title

    def __repr__(self):
        return self.title


class MockSubreddit:
    def __init__(self, display_name: str, *args, **kwargs):
        self.display_name = display_name

    def __repr__(self):
        return self.display_name

    def controversial(self, *args, **kwargs):
        return [MockSubmission('controversial') for _ in range(kwargs['limit'])]

    def gilded(self, *args, **kwargs):
        return [MockSubmission('gilded') for _ in range(kwargs['limit'])]

    def hot(self, *args, **kwargs):
        return [MockSubmission('hot') for _ in range(kwargs['limit'])]

    def new(self, *args, **kwargs):
        return [MockSubmission('new') for _ in range(kwargs['limit'])]

    def random_rising(self, *args, **kwargs):
        return [MockSubmission('random_rising') for _ in range(kwargs['limit'])]

    def rising(self, *args, **kwargs):
        return [MockSubmission('rising') for _ in range(kwargs['limit'])]

    def top(self, *args, **kwargs):
        return [MockSubmission('top') for _ in range(kwargs['limit'])]


class MockReddit:
    def __init__(self, *args, **kwargs):
        self.user = MockRedditor()
        self.subreddit = MockSubreddit


@pytest.fixture()
def mock_reddit(monkeypatch):
    monkeypatch.setattr(praw, 'Reddit', MockReddit)


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

    def it_gets_three_controversial_posts(self, mock_reddit):
        cli = RedditCli('tests/.exampleconfig')
        result = cli.post(subreddit='testsubreddit', post_sorting='controversial', limit=3)
        expected = ['##### *Controversial Posts from r/testsubreddit'] + ['- *controversial*'] * 3

    def it_gets_three_gilded_posts(self, mock_reddit):
        cli = RedditCli('tests/.exampleconfig')
        result = cli.post(subreddit='testsubreddit', post_sorting='gilded', limit=3)
        expected = ['##### *Controversial Posts from r/testsubreddit'] + ['- *controversial*'] * 3
