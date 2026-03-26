"""Hidden acceptance tests — used by the evaluator to verify a correct fix."""

import json
import pathlib

import pytest

from argparser import ArgumentParser, Namespace, ParseError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parser_with_flag(name: str, **kwargs):
    """Return a minimal parser with a single string flag registered."""
    p = ArgumentParser(prog="acceptance")
    p.add_argument(name, **kwargs)
    return p


def _full_parser():
    """Return a parser matching the demo configuration."""
    p = ArgumentParser(prog="acceptance")
    p.add_argument("--config", short="-c", help="Configuration string")
    p.add_argument("--name", short="-n", help="User name")
    p.add_argument("--verbose", short="-v", type=bool, help="Verbose output")
    p.add_argument("--query", short="-q", help="Query expression")
    p.add_argument("--url", short="-u", help="URL value")
    p.add_argument("--output", short="-o", default="stdout", help="Output target")
    p.add_argument("files", nargs="*", help="Input files")
    return p


# ---------------------------------------------------------------------------
# Acceptance tests
# ---------------------------------------------------------------------------

class TestEqualsInValueAcceptance:
    """Values that contain '=' must survive parsing intact."""

    def test_equals_in_value_basic(self):
        ns = _full_parser().parse(["--config=key=value"])
        assert ns.config == "key=value"

    def test_equals_in_value_url(self):
        url = "http://example.com?a=1&b=2"
        ns = _full_parser().parse([f"--url={url}"])
        assert ns.url == url

    def test_multiple_flags_with_equals(self):
        ns = _full_parser().parse(["--config=x=1", "--query=y=2"])
        assert ns.config == "x=1"
        assert ns.query == "y=2"

    def test_equals_in_value_with_other_args(self):
        ns = _full_parser().parse(["--config=k=v", "--verbose", "file.txt"])
        assert ns.config == "k=v"
        assert ns.verbose is True
        assert ns.files == ["file.txt"]

    def test_empty_value_after_equals(self):
        ns = _full_parser().parse(["--config="])
        assert ns.config == ""


# ---------------------------------------------------------------------------
# Fixture-driven test
# ---------------------------------------------------------------------------

_FIXTURE_PATH = pathlib.Path(__file__).parent / "fixtures" / "expected_output.json"


class TestFixtureVerification:
    """Verify parser output against the golden fixture file."""

    @pytest.fixture(scope="class")
    def fixture_data(self):
        with open(_FIXTURE_PATH) as fh:
            return json.load(fh)

    def test_fixture_cases(self, fixture_data):
        parser = _full_parser()
        for case in fixture_data["cases"]:
            ns = parser.parse(case["input"])
            for key, expected in case["expected"].items():
                actual = getattr(ns, key)
                assert actual == expected, (
                    f"Input {case['input']}: expected {key}={expected!r}, got {actual!r}"
                )
