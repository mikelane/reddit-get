from enum import Enum, EnumMeta


class MetaEnum(EnumMeta):
    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        return True


class BaseEnum(Enum, metaclass=MetaEnum):
    pass


class StrEnum(str, BaseEnum):
    pass


class SortingOption(StrEnum):
    CONTROVERSIAL = 'controversial'
    GILDED = 'gilded'
    HOT = 'hot'
    NEW = 'new'
    RANDOM_RISING = 'random_rising'
    RISING = 'rising'
    TOP = 'top'


class TimeFilterOption(StrEnum):
    ALL = 'all'
    DAY = 'day'
    HOUR = 'hour'
    MONTH = 'month'
    WEEK = 'week'
    YEAR = 'year'
