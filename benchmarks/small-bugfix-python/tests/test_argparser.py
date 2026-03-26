"""Unit tests for the argparser module."""

import pytest

from argparser import ArgumentParser, Namespace, ParseError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_parser(**extra_flags):
    """Return a pre-configured parser for most tests."""
    p = ArgumentParser(prog="test")
    p.add_argument("--name", short="-n", help="A name value")
    p.add_argument("--config", short="-c", help="Config string")
    p.add_argument("--verbose", short="-v", type=bool, help="Verbose mode")
    p.add_argument("--query", short="-q", help="Query expression")
    p.add_argument("files", nargs="*", help="Input files")
    return p


# ---------------------------------------------------------------------------
# PASSING — the bug does not affect these paths
# ---------------------------------------------------------------------------

class TestBasicParsing:
    """Core parsing paths that work correctly."""

    def test_long_flag_with_space(self):
        """--name world  →  name='world'"""
        ns = _make_parser().parse(["--name", "world"])
        assert ns.name == "world"

    def test_short_flag(self):
        """-n world  →  name='world'"""
        ns = _make_parser().parse(["-n", "world"])
        assert ns.name == "world"

    def test_boolean_flag(self):
        """--verbose  →  verbose=True (no value consumed)."""
        ns = _make_parser().parse(["--verbose"])
        assert ns.verbose is True

    def test_positional_args(self):
        """Bare tokens are collected as positional values."""
        ns = _make_parser().parse(["file1.txt", "file2.txt"])
        assert ns.files == ["file1.txt", "file2.txt"]

    def test_double_dash_stops_parsing(self):
        """Everything after -- is treated as a positional argument."""
        ns = _make_parser().parse(["--", "--not-a-flag", "-x"])
        assert ns.files == ["--not-a-flag", "-x"]

    def test_combined_short_flags(self):
        """-abc expands to -a -b -c (all boolean)."""
        p = ArgumentParser(prog="test")
        p.add_argument("--alpha", short="-a", type=bool)
        p.add_argument("--bravo", short="-b", type=bool)
        p.add_argument("--charlie", short="-c", type=bool)
        ns = p.parse(["-abc"])
        assert ns.alpha is True
        assert ns.bravo is True
        assert ns.charlie is True


# ---------------------------------------------------------------------------
# FAILING — exposed by the equals-sign splitting bug
# ---------------------------------------------------------------------------

class TestEqualsInValue:
    """Flags whose *values* contain '=' characters."""

    def test_long_flag_equals_with_equals_in_value(self):
        """--config=key=value  →  config='key=value'

        The parser must split only on the *first* '=' so that the remainder
        is preserved as the flag's value.
        """
        ns = _make_parser().parse(["--config=key=value"])
        assert ns.config == "key=value"

    def test_long_flag_equals_with_multiple_equals(self):
        """--query=a=1&b=2  →  query='a=1&b=2'"""
        ns = _make_parser().parse(["--query=a=1&b=2"])
        assert ns.query == "a=1&b=2"
