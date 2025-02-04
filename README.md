# polars-lprof

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
the performance reports:

```bash
plprof profile_output_2025-02-04T002856.txt
```
