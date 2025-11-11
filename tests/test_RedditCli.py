from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import fire
from praw.exceptions import RedditAPIException, RedditErrorItem
import pytest

from reddit_get import RedditCli


class TestRedditCli:
    def it_sets_up_the_configs(self, mock_reddit):
        cli = RedditCli('tests/.exampleconfig')
        assert cli.configs['reddit-get']['client_id'] == 'testid'
        assert cli.configs['reddit-get']['client_secret'] == 'testsecret'
        assert cli.configs['reddit-get']['username'] == 'testusername'
        assert cli.configs['reddit-get']['password'] == 'testpassword'

    def it_returns_the_config_file_path_in_use(self, mock_reddit):
        cli = RedditCli('tests/.exampleconfig')
        assert cli.config_location() == Path('tests/.exampleconfig').resolve()

    class TestErrors:
        def it_handles_invalid_toml_files(self):
            with pytest.raises(fire.core.FireError):
                RedditCli('tests/.invalitomlfile')

        def it_handles_missing_config_files(self):
            with pytest.raises(fire.core.FireError):
                RedditCli('tests/.filedoesnotexist')

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

    class TestPost:
        class TestBasicPostOutput:
            def it_gets_three_controversial_posts(self, mock_reddit):
                cli = RedditCli('tests/.exampleconfig')
                result = cli.post(subreddit='testsubreddit', post_sorting='controversial', limit=3)
                expected = ['#### The Most Controversial Posts for All Time from r/testsubreddit'] + [
                    '- controversial',
                ] * 3
                assert result == expected

            def it_gets_three_gilded_posts(self, mock_reddit):
                cli = RedditCli('tests/.exampleconfig')
                result = cli.post(subreddit='testsubreddit', post_sorting='gilded', limit=3)
                expected = ['#### The Most Awarded Posts for All Time from r/testsubreddit'] + [
                    '- gilded',
                ] * 3
                assert result == expected

            def it_gets_hot_posts(self, mock_reddit):
                cli = RedditCli('tests/.exampleconfig')
                result = cli.post(subreddit='testsubreddit', post_sorting='hot', limit=3)
                expected = ['#### The Hottest Posts for All Time from r/testsubreddit'] + ['- hot'] * 3
                assert result == expected

            def it_gets_new_posts(self, mock_reddit):
                cli = RedditCli('tests/.exampleconfig')
                result = cli.post(subreddit='testsubreddit', post_sorting='new', limit=3)
                expected = ['#### The Newest Posts for All Time from r/testsubreddit'] + ['- new'] * 3
                assert result == expected

            def it_gets_random_rising_posts(self, mock_reddit):
                cli = RedditCli('tests/.exampleconfig')
                result = cli.post(subreddit='testsubreddit', post_sorting='random_rising', limit=3)
                expected = ['#### The Randomly Selected Rising Posts for All Time from r/testsubreddit'] + [
                    '- random_rising',
                ] * 3
                assert result == expected

            def it_gets_rising_posts(self, mock_reddit):
                cli = RedditCli('tests/.exampleconfig')
                result = cli.post(subreddit='testsubreddit', post_sorting='rising', limit=3)
                expected = ['#### The Rising Posts for All Time from r/testsubreddit'] + ['- rising'] * 3
                assert result == expected

            def it_gets_top_posts(self, mock_reddit):
                cli = RedditCli('tests/.exampleconfig')
                result = cli.post(subreddit='testsubreddit', post_sorting='top', limit=3)
                expected = ['#### The Top Posts for All Time from r/testsubreddit'] + ['- top'] * 3
                assert result == expected

        class TestCustomHeaderOutput:
            def it_returns_custom_header_with_no_options(self):
                cli = RedditCli('tests/.exampleconfig')
                result = cli.post(
                    subreddit='testsubreddit', post_sorting='top', limit=3, custom_header='Test Header',
                )
                expected = ['Test Header'] + ['- top'] * 3
                assert result == expected

            def it_returns_custom_header_with_one_options(self):
                cli = RedditCli('tests/.exampleconfig')
                result = cli.post(
                    subreddit='testsubreddit', post_sorting='top', limit=3, custom_header='Test {sorting}',
                )
                expected = ['Test Top'] + ['- top'] * 3
                assert result == expected

            def it_returns_custom_header_with_two_options(self):
                cli = RedditCli('tests/.exampleconfig')
                result = cli.post(
                    subreddit='testsubreddit',
                    post_sorting='top',
                    limit=3,
                    custom_header='Test {sorting} and {time}',
                )
                expected = ['Test Top and All Time'] + ['- top'] * 3
                assert result == expected

            def it_returns_custom_header_with_all_options(self):
                cli = RedditCli('tests/.exampleconfig')
                result = cli.post(
                    subreddit='testsubreddit',
                    post_sorting='top',
                    limit=3,
                    custom_header='Test {sorting}, {time}, and {subreddit}',
                )
                expected = ['Test Top, All Time, and r/testsubreddit'] + ['- top'] * 3
                assert result == expected

            class TestHeaderError:
                def it_returns_an_error_for_invalid_header_keywords(self):
                    with pytest.raises(fire.core.FireError):
                        cli = RedditCli('tests/.exampleconfig')
                        result = cli.post(
                            subreddit='testsubreddit', post_sorting='top', limit=3, custom_header='{invalid}',
                        )

        class TestCustomPostOutput:
            def it_returns_post_output_with_a_single_keyword(self):
                cli = RedditCli('tests/.exampleconfig')
                result = cli.post(
                    subreddit='testsubreddit', post_sorting='top', limit=3, output_format='test {title}',
                )
                expected = ['#### The Top Posts for All Time from r/testsubreddit'] + ['test top'] * 3
                assert result == expected

            def it_returns_post_output_with_multiple_keywords(self):
                cli = RedditCli('tests/.exampleconfig')
                result = cli.post(
                    subreddit='testsubreddit',
                    post_sorting='top',
                    limit=3,
                    output_format='test {title} - {author}',
                )
                expected = ['#### The Top Posts for All Time from r/testsubreddit'] + [
                    'test top - testauthor',
                ] * 3
                assert result == expected

            class TestCustomPostOutputErrors:
                def it_raises_fire_error_for_invalid_template_key(self):
                    with pytest.raises(fire.core.FireError):
                        cli = RedditCli('tests/.exampleconfig')
                        result = cli.post(
                            subreddit='testsubreddit',
                            post_sorting='top',
                            limit=3,
                            output_format='{invalid}',
                        )

                def it_raises_fire_error_for_template_with_no_keys(self):
                    with pytest.raises(fire.core.FireError):
                        cli = RedditCli('tests/.exampleconfig')
                        result = cli.post(
                            subreddit='testsubreddit',
                            post_sorting='top',
                            limit=3,
                            output_format='Nothing here',
                        )


class TestRetryLogic:
    """Tests for _execute_with_retry method including rate limit handling."""

    def it_succeeds_on_first_attempt(self, mock_reddit):
        """Test successful execution on first attempt."""
        cli = RedditCli('tests/.exampleconfig')
        result = cli._execute_with_retry(lambda: 'success')
        assert result == 'success'

    def it_retries_on_rate_limit_and_succeeds(self, mock_reddit):
        """Test exponential backoff retry logic for rate limit errors."""
        cli = RedditCli('tests/.exampleconfig')

        # Create a proper RedditAPIException with RATELIMIT error
        rate_limit_item = RedditErrorItem(
            error_type='RATELIMIT', message='You are doing that too much', field=''
        )

        # Function that fails twice with rate limit, then succeeds
        attempt_count = [0]

        def flaky_function():
            attempt_count[0] += 1
            if attempt_count[0] <= 2:
                exception = RedditAPIException([rate_limit_item])
                raise exception
            return 'success'

        with patch('time.sleep') as mock_sleep:
            result = cli._execute_with_retry(flaky_function, max_retries=3)
            assert result == 'success'
            # Verify exponential backoff: 2^0=1s, 2^1=2s
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(1)
            mock_sleep.assert_any_call(2)

    def it_raises_error_after_max_retries_on_rate_limit(self, mock_reddit):
        """Test that rate limit error is raised after max retries exceeded."""
        cli = RedditCli('tests/.exampleconfig')

        # Create a proper RedditAPIException with RATELIMIT error
        rate_limit_item = RedditErrorItem(
            error_type='RATELIMIT', message='You are doing that too much', field=''
        )

        def always_fails():
            exception = RedditAPIException([rate_limit_item])
            raise exception

        with patch('time.sleep'):
            with pytest.raises(fire.core.FireError, match='Reddit API rate limit exceeded'):
                cli._execute_with_retry(always_fails, max_retries=3)

    def it_handles_other_reddit_api_errors(self, mock_reddit):
        """Test handling of non-rate-limit Reddit API errors."""
        cli = RedditCli('tests/.exampleconfig')

        # Create a proper RedditAPIException with a different error type
        error_item = RedditErrorItem(
            error_type='OTHER_ERROR', message='Some other error occurred', field=''
        )

        def fails_with_other_error():
            exception = RedditAPIException([error_item])
            raise exception

        with pytest.raises(fire.core.FireError, match='Reddit API error: OTHER_ERROR: Some other error occurred'):
            cli._execute_with_retry(fails_with_other_error, max_retries=3)


class TestRedditAPIErrorHandling:
    """Tests for Reddit API error handling in post method."""

    def it_handles_nonexistent_subreddit_error(self, mock_reddit):
        """Test error handling for non-existent subreddit."""
        cli = RedditCli('tests/.exampleconfig')

        # Create a proper RedditAPIException with SUBREDDIT_NOEXIST error
        error_item = RedditErrorItem(
            error_type='SUBREDDIT_NOEXIST', message='Subreddit not found', field=''
        )

        # Patch the subreddit method to raise the exception
        with patch.object(cli.reddit, 'subreddit') as mock_subreddit:
            mock_subreddit.side_effect = RedditAPIException([error_item])

            with pytest.raises(fire.core.FireError, match="Subreddit 'r/nonexistent' does not exist"):
                cli.post(subreddit='nonexistent', limit=3)

    def it_handles_private_subreddit_error(self, mock_reddit):
        """Test error handling for private/restricted subreddit."""
        cli = RedditCli('tests/.exampleconfig')

        # Create a proper RedditAPIException with SUBREDDIT_NOTALLOWED error
        error_item = RedditErrorItem(
            error_type='SUBREDDIT_NOTALLOWED', message='Subreddit is private', field=''
        )

        # Patch the subreddit method to raise the exception
        with patch.object(cli.reddit, 'subreddit') as mock_subreddit:
            mock_subreddit.side_effect = RedditAPIException([error_item])

            with pytest.raises(fire.core.FireError, match="does not exist or is private/restricted"):
                cli.post(subreddit='privatesubreddit', limit=3)

    def it_handles_rate_limit_during_post_fetch(self, mock_reddit):
        """Test rate limit handling during post fetching."""
        cli = RedditCli('tests/.exampleconfig')

        # Create a proper RedditAPIException with RATELIMIT error
        rate_limit_item = RedditErrorItem(
            error_type='RATELIMIT', message='You are doing that too much', field=''
        )

        # Create a counter to track attempts
        attempt_count = [0]

        # Create a mock subreddit that fails once with rate limit, then succeeds
        def mock_top(*args, **kwargs):
            attempt_count[0] += 1
            if attempt_count[0] == 1:
                raise RedditAPIException([rate_limit_item])
            return [Mock(title='post1'), Mock(title='post2'), Mock(title='post3')]

        with patch.object(cli.reddit, 'subreddit') as mock_subreddit_method:
            mock_subreddit_obj = Mock()
            mock_subreddit_obj.top = mock_top
            mock_subreddit_method.return_value = mock_subreddit_obj

            with patch('time.sleep'):
                result = cli.post(subreddit='testsubreddit', limit=3)
                # Should succeed after retry
                assert len(result) == 4  # header + 3 posts
                assert attempt_count[0] == 2  # Failed once, succeeded on retry

    def it_re_raises_non_subreddit_api_errors_from_post_method(self, mock_reddit):
        """Test that non-subreddit API errors are re-raised to _execute_with_retry."""
        cli = RedditCli('tests/.exampleconfig')

        # Create a RedditAPIException with a different error (not subreddit related)
        error_item = RedditErrorItem(
            error_type='INVALID_OPTION', message='Invalid parameter provided', field=''
        )

        # Mock the subreddit to raise the exception during query execution
        with patch.object(cli.reddit, 'subreddit') as mock_subreddit_method:
            mock_subreddit_obj = Mock()
            mock_subreddit_obj.top.side_effect = RedditAPIException([error_item])
            mock_subreddit_method.return_value = mock_subreddit_obj

            # Should be caught and re-raised by post, then handled by _execute_with_retry
            with pytest.raises(fire.core.FireError, match='Reddit API error: INVALID_OPTION'):
                cli.post(subreddit='testsubreddit', limit=3)
