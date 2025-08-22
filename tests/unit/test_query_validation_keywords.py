import pytest

from app.query_validation import remove_keywords_duplicates


def test_remove_author_tokens():
    names = ["Ernest Hemingway", "Paris"]
    filters = {"author": ["Ernest Hemingway"]}

    remove_keywords_duplicates(names, filters)

    assert names == ["Paris"]


def test_remove_years_and_pages():
    names = ["2019", "Some Place", "300"]
    filters = {"published_year": {"min": 2010, "max": 2019, "exact": None}, "pages_min": 300}

    remove_keywords_duplicates(names, filters)

    assert names == ["Some Place"]


def test_case_insensitive_and_deduplication():
    names = ["Paris", "paris", "PARIS", "London"]
    filters = {"author": ["someone else"]}  # unrelated filter

    # function should deduplicate case-insensitively and preserve first occurrence
    remove_keywords_duplicates(names, filters)

    # Only one 'Paris' should remain (first occurrence), plus 'London'
    assert names == ["Paris", "London"]


def test_non_string_items_and_numeric_filters():
    names = ["123", "456", "Beach"]
    filters = {"pages_max": 123}

    # Should remove the string '123' but leave the integer 456 untouched
    remove_keywords_duplicates(names, filters)

    assert names == ["456", "Beach"]


def test_empty_names_no_error():
    names = []
    filters = {"author": ["Someone"]}

    # Should not raise and list remains empty
    remove_keywords_duplicates(names, filters)
    assert names == []
