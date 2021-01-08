import praw
import pytest


@pytest.fixture(scope='session')
def monkeysession(request):
    from _pytest.monkeypatch import MonkeyPatch

    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


# noinspection PyMethodMayBeStatic
class MockRedditor:
    def me(self):
        return 'Mocked Redditor'


class MockSubmission:
    def __init__(self, title):
        self.title = title


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
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


# noinspection PyUnusedLocal
class MockReddit:
    def __init__(self, *args, **kwargs):
        self.user = MockRedditor()
        self.subreddit = MockSubreddit


@pytest.fixture(scope='session', autouse=True)
def mock_reddit(monkeysession):
    monkeysession.setattr(praw, 'Reddit', MockReddit)
