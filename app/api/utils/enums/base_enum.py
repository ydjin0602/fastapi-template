from enum import Enum
from typing import Any
from typing import Self


class BaseENUM(Enum):
    @classmethod
    def _missing_(cls, value: Any) -> Self | None:
        for member in cls:
            if isinstance(value, str) and member.value == value.upper():
                return member

        return None

    @classmethod
    def keys(cls) -> list[str]:
        """Returns a list of all the enum keys."""
        return cls._member_names_

    @classmethod
    def values(cls) -> list[Any]:
        """Returns a list of all the enum values."""
        return list(cls._value2member_map_.keys())

    @classmethod
    def to_dict(cls) -> dict[str, dict[str, Any]]:
        """Return enum as dict."""
        return {cls.__name__: {member.name: member.value for member in cls}}
