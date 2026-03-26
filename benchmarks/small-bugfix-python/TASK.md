# Task: Fix the Argument Parser

Fix the argument parser so flags with `=` in their values are handled correctly.

## Problem
The argument parser in `argparser.py` silently drops parts of flag values that contain `=` signs.
For example, `--config=key=value` should parse as `config="key=value"` but currently parses as `config="key"`.

## Requirements
- All tests in `tests/` should pass
- Do not break any existing functionality
- Keep the fix minimal — don't restructure the entire parser

## Files
- `argparser.py` — the argument parser implementation (contains the bug)
- `tests/test_argparser.py` — test suite
