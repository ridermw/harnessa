# argparser

A lightweight command-line argument parser written in pure Python (no dependencies).

## Features

- Long flags: `--name=value`, `--name value`
- Short flags: `-n value`, `-nVALUE`
- Boolean flags: `--verbose`
- Combined short flags: `-abc` → `-a -b -c`
- Positional arguments
- `--` separator to stop flag parsing
- Auto-generated help text

## Quick start

```python
from argparser import ArgumentParser

parser = ArgumentParser(prog="myapp", description="Process some files.")
parser.add_argument("--config", short="-c", help="Config string")
parser.add_argument("--verbose", short="-v", type=bool, help="Enable verbose output")
parser.add_argument("files", nargs="*", help="Input files")

ns = parser.parse(["--config=production", "--verbose", "data.csv"])
print(ns.config)    # "production"
print(ns.verbose)   # True
print(ns.files)     # ["data.csv"]
```

## CLI demo

```bash
python argparser.py --name Alice --verbose file1.txt file2.txt
python argparser.py --help
```

## Running tests

```bash
pytest tests/
```
