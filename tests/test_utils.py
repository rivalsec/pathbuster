import pytest
from pathbuster.utils.common import count_lines, count_words

def test_count_lines():
    assert count_lines("Hello\nWorld") == 2
    assert count_lines("Hello World") == 1
    assert count_lines("") == 1
    assert count_lines("\n\n\n") == 4

def test_count_words():
    assert count_words("Hello World") == 2
    assert count_words("Hello") == 1
    assert count_words("") == 1
    assert count_words("Hello big World") == 3
