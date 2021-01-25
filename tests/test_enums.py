import pytest

from reddit_get import SortingOption


class TestEnums:
    def it_raises_an_error_for_invalid_sorting_options(self):
        with pytest.raises(ValueError):
            SortingOption('invalid')

    def it_returns_true_if_value_in_sorting_option(self):
        assert 'top' in SortingOption

    def it_returns_false_if_value_not_in_sorting_option(self):
        assert 'invalid' not in SortingOption
