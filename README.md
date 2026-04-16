# polars-lprof

<!-- [![downloads](https://static.pepy.tech/badge/polars-lprof/month)](https://pepy.tech/project/polars-lprof) -->
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![PyPI](https://img.shields.io/pypi/v/polars-lprof.svg)](https://pypi.org/project/polars-lprof)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/polars-lprof.svg)](https://pypi.org/project/polars-lprof)
[![License](https://img.shields.io/pypi/l/polars-lprof.svg)](https://pypi.python.org/pypi/polars-lprof)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/lmmx/polars-lprof/master.svg)](https://results.pre-commit.ci/latest/github/lmmx/polars-lprof/master)

Read `line_profiler` reports into Polars DataFrames

## Installation

The `polars-lprof` package can be installed with either `polars` or `polars-lts-cpu` using the extras
by those names:

```bash
pip install polars-lprof[polars]
pip install polars-lprof[polars-lts-cpu]
```

If Polars is already installed, you can simply `pip install polars-lprof`.

## Usage

> Note: use this tool after running Python code with `@line_profiler.profile` decorators on
> functions which will output `.txt` plain text reports on the program's performance. The
> `line_profiler` tool relies on the environment variable set with `export LINE_PROFILE=1`.

First run your `line_profiler` (in whichever variations you want) and then use this tool to analyse
the performance reports (named like `profile_output_2025-02-04T002856.txt`). The most recent one
will always be called `profile_output.txt` but often we want to collect multiple for review.

```bash
plprof profile_output.txt
```

Use it from Python as a library:

```python
from plprof import parse_lprof

metadata, lines = parse_lprof("profile_output.txt")
```
