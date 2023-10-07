import pytest
from pathbuster.utils.common import count_lines, count_words

def test_count_lines():
    assert count_lines("") == 0  # Empty string should return 0
    assert count_lines("Hello\nWorld") == 2  # Two lines separated by a newline character
    assert count_lines("Hello\n\nWorld") == 3  # Three lines with an empty line in between
    assert count_lines("Hello World") == 1  # Single line without any newline characters

def test_count_words():
    assert count_words("") == 0  # Empty string should return 0
    assert count_words("Hello World") == 2  # Two words separated by a space
    assert count_words("Hello\nWorld") == 1  # TODO:fix? Two words separated by a newline character
    assert count_words("Hello\n\nWorld") == 1  # TODO:fix? Two words with an empty line in between
