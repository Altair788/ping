"""Тесты для validate_url — чистая функция, без сети."""

import sys
from argparse import ArgumentTypeError
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ping import validate_url


def test_valid_https() -> None:
    assert validate_url("https://example.com/x.bin") == "https://example.com/x.bin"


def test_valid_http() -> None:
    assert validate_url("http://example.com") == "http://example.com"


def test_rejects_ftp_scheme() -> None:
    import pytest

    with pytest.raises(ArgumentTypeError):
        validate_url("ftp://example.com")


def test_rejects_empty_string() -> None:
    import pytest

    with pytest.raises(ArgumentTypeError):
        validate_url("")


def test_rejects_garbage() -> None:
    import pytest

    with pytest.raises(ArgumentTypeError):
        validate_url("not a url")


def test_rejects_empty_netloc() -> None:
    import pytest

    with pytest.raises(ArgumentTypeError):
        validate_url("https://")
