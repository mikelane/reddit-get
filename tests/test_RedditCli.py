from pathlib import Path

import fire
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
                    '- controversial'
                ] * 3
                assert result == expected

            def it_gets_three_gilded_posts(self, mock_reddit):
                cli = RedditCli('tests/.exampleconfig')
                result = cli.post(subreddit='testsubreddit', post_sorting='gilded', limit=3)
                expected = ['#### The Most Awarded Posts for All Time from r/testsubreddit'] + [
                    '- gilded'
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
                    '- random_rising'
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
                    subreddit='testsubreddit', post_sorting='top', limit=3, custom_header='Test Header'
                )
                expected = ['Test Header'] + ['- top'] * 3
                assert result == expected

            def it_returns_custom_header_with_one_options(self):
                cli = RedditCli('tests/.exampleconfig')
                result = cli.post(
                    subreddit='testsubreddit', post_sorting='top', limit=3, custom_header='Test {sorting}'
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
                            subreddit='testsubreddit', post_sorting='top', limit=3, custom_header='{invalid}'
                        )

        class TestCustomPostOutput:
            def it_returns_post_output_with_a_single_keyword(self):
                cli = RedditCli('tests/.exampleconfig')
                result = cli.post(
                    subreddit='testsubreddit', post_sorting='top', limit=3, output_format='test {title}'
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
                    'test top - testauthor'
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
