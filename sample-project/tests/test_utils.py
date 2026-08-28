"""The only tests in the project. Deliberately thin."""

from utils import slugify, truncate


def test_slugify_basic():
    assert slugify("Hello World") == "hello-world"


def test_slugify_strips_punctuation():
    assert slugify("Notes: v2.0!") == "notes-v2-0"


def test_truncate_short_text_unchanged():
    assert truncate("short") == "short"
