from __future__ import annotations

from collections.abc import Mapping
from typing import Final

CHARACTER_CLASS_SPECIAL_CHARACTERS: Final[str] = '-[\\]^'
COMMON_SPECIAL_CHARACTERS: Final[str] = 'fnrtv'
DOUBLE_QUOTED_LITERAL_SPECIAL_CHARACTERS: Final[str] = '"\\'
SINGLE_QUOTED_LITERAL_SPECIAL_CHARACTERS: Final[str] = "'\\"
COMMON_SPECIAL_CHARACTERS_TRANSLATION_TABLE: Final[Mapping[int, str]] = {
    ord(('\\' + character).encode('utf-8').decode('unicode-escape')): '\\'
    + character
    for character in COMMON_SPECIAL_CHARACTERS
}

assert len(
    non_special_characters := [
        character
        for character in COMMON_SPECIAL_CHARACTERS
        if len(('\\' + character).encode('unicode-escape').decode('utf-8'))
        != 1
    ]
), non_special_characters
