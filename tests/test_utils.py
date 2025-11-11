from __future__ import annotations

import os

import fire
import pytest

from reddit_get import (
    RedditCli,
    get_post_sorting_option,
    get_reddit_query_function,
)
from reddit_get.utils import load_configs


class TestLoadConfigs:
    """Tests for OAuth2 environment variable authentication and config file validation."""

    class TestEnvironmentVariableAuthentication:
        def it_loads_credentials_from_environment_variables(self, monkeypatch):
            """Test OAuth2 environment variable authentication path."""
            monkeypatch.setenv('REDDIT_CLIENT_ID', 'env_client_id')
            monkeypatch.setenv('REDDIT_CLIENT_SECRET', 'env_client_secret')
            monkeypatch.setenv('REDDIT_USER_AGENT', 'env_user_agent')

            config_path, configs = load_configs('~/.redditgetrc')

            assert configs['reddit-get']['client_id'] == 'env_client_id'
            assert configs['reddit-get']['client_secret'] == 'env_client_secret'
            assert configs['reddit-get']['user_agent'] == 'env_user_agent'

        def it_uses_default_user_agent_when_not_set(self, monkeypatch):
            """Test default user agent when only client_id and client_secret are set."""
            monkeypatch.setenv('REDDIT_CLIENT_ID', 'env_client_id')
            monkeypatch.setenv('REDDIT_CLIENT_SECRET', 'env_client_secret')
            # Don't set REDDIT_USER_AGENT - should use default 'reddit-get/1.1.0'

            config_path, configs = load_configs('~/.redditgetrc')

            assert configs['reddit-get']['client_id'] == 'env_client_id'
            assert configs['reddit-get']['client_secret'] == 'env_client_secret'
            assert configs['reddit-get']['user_agent'] == 'reddit-get/1.1.0'

    class TestConfigFileValidation:
        def it_raises_error_for_missing_reddit_get_section(self, tmp_path, monkeypatch):
            """Test error when config file is missing [reddit-get] section."""
            # Clear environment variables to force config file usage
            monkeypatch.delenv('REDDIT_CLIENT_ID', raising=False)
            monkeypatch.delenv('REDDIT_CLIENT_SECRET', raising=False)
            monkeypatch.delenv('REDDIT_USER_AGENT', raising=False)

            config_file = tmp_path / 'config.toml'
            config_file.write_text('[other-section]\nkey = "value"\n')

            with pytest.raises(fire.core.FireError, match='missing \\[reddit-get\\] section'):
                load_configs(str(config_file))

        def it_raises_error_for_missing_required_keys(self, monkeypatch):
            """Test error when config file is missing required keys."""
            # Clear environment variables to force config file usage
            monkeypatch.delenv('REDDIT_CLIENT_ID', raising=False)
            monkeypatch.delenv('REDDIT_CLIENT_SECRET', raising=False)
            monkeypatch.delenv('REDDIT_USER_AGENT', raising=False)

            with pytest.raises(fire.core.FireError, match='missing required keys'):
                load_configs('tests/.configwithmissingoptions')

        def it_raises_error_for_missing_file_without_env_vars(self, monkeypatch):
            """Test error when config file not found and environment variables not set."""
            # Clear environment variables
            monkeypatch.delenv('REDDIT_CLIENT_ID', raising=False)
            monkeypatch.delenv('REDDIT_CLIENT_SECRET', raising=False)
            monkeypatch.delenv('REDDIT_USER_AGENT', raising=False)

            with pytest.raises(
                fire.core.FireError,
                match='No valid TOML config found.*and required environment variables not set',
            ):
                load_configs('tests/.filedoesnotexist')

        def it_raises_error_for_invalid_toml_syntax(self, monkeypatch):
            """Test error handling for invalid TOML syntax."""
            # Clear environment variables to force config file usage
            monkeypatch.delenv('REDDIT_CLIENT_ID', raising=False)
            monkeypatch.delenv('REDDIT_CLIENT_SECRET', raising=False)
            monkeypatch.delenv('REDDIT_USER_AGENT', raising=False)

            with pytest.raises(fire.core.FireError, match='Invalid TOML syntax'):
                load_configs('tests/.invalidtomlfile')


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
