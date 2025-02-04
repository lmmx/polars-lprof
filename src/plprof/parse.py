from pathlib import Path
from typing import Tuple

import polars as pl


def parse_lprof(
    source_file: Path, merge_metadata: bool = False
) -> tuple[pl.DataFrame, pl.DataFrame] | pl.DataFrame:
    # Read file with row numbers and filter out empty lines
    df = (
        pl.read_csv(
            source_file, separator="\x1e", has_header=False, new_columns=["line"]
        )
        .with_row_index("row_number")
        .filter(pl.col("line").str.strip_chars().is_not_null())
    )

    # Find the separator line index using verbose regex
    separator_pattern = r"""(?x)
        ^\s*         # Start with optional whitespace
        ={5,}        # Five or more equals signs
        \s*$         # Optional whitespace until end of line
    """
    separator_idx = (
        df.select(
            pl.col("row_number"),
            pl.col("line").str.contains(separator_pattern, literal=False),
        )
        .filter(pl.col("line"))
        .get_column("row_number")
        .min()
    )

    if separator_idx is None:
        return pl.DataFrame()

    # Split into header and data sections
    header_df = df.filter(pl.col("row_number") < separator_idx)
    data_df = df.filter(pl.col("row_number") > separator_idx)

    # Parse header metadata with verbose regex
    metadata_pattern = r"""(?x)
        ^
        (Timer\ unit|Total\ time|File|Function):\s+
        (.+?)
        (?:\s+\{\s+.+\}\s*)?  # Optional code context
        $
    """
    metadata = (
        header_df.select(pl.col("line").str.extract_groups(metadata_pattern))
        .unnest("line")
        .filter(pl.col("1").is_not_null())
        .with_columns(dummy_index=pl.lit(0))  # Add dummy index for pivot
        .pivot(
            index="dummy_index",
            on="1",
            values="2",
            aggregate_function="first",
        )
        .drop("dummy_index")
    )
    # metadata = (
    #     header_df.select(pl.col("line").str.extract_groups(metadata_pattern))
    #     .unnest("line")
    #     .filter(pl.col("1").is_not_null())
    #     .pivot(index=[], columns="1", values="2", aggregate_function="first")
    # )
    print("Metadata:", metadata)

    # Parse column positions from header line
    header_line = (
        df.filter(pl.col("row_number") == separator_idx - 1).get_column("line").first()
    )

    # Find column boundaries based on header spacing
    cols = []
    prev_end = 0
    headers = ["Line #", "Hits", "Time", "Per Hit", "% Time", "Line Contents"]
    for header in headers[:-1]:
        start = header_line.find(header, prev_end)
        end = header_line.find(headers[headers.index(header) + 1], start)
        cols.append((start, end))
        prev_end = end
    cols.append((prev_end, None))  # Last column goes to end of line

    # Create regex pattern for data lines with verbose formatting
    data_pattern = r"""(?x)
        ^
        (?:  # Optional line number and code indentation
            \s*(?P<line_num>\d+)\s+ 
            (?P<hits>\d+)\s+ 
            (?P<time>[\d.]+)\s+ 
            (?P<per_hit>[\d.]+)\s+ 
            (?P<percent_time>[\d.]+)\s+ 
            (?P<contents>.*) 
        )
    """

    # Process data lines with explicit schema
    parsed_data = (
        data_df.select(pl.col("line").str.extract_groups(data_pattern))
        .unnest("line")
        .select(
            [
                pl.col("line_num").cast(pl.UInt32),
                pl.col("hits").cast(pl.UInt32),
                pl.col("time").cast(pl.Float64),
                pl.col("per_hit").cast(pl.Float64),
                pl.col("percent_time").cast(pl.Float64),
                pl.col("contents").str.strip_chars().alias("line_contents"),
            ]
        )
    )
    # print("Parsed data:", parsed_data)

    # Add metadata as columns
    tu_col = pl.lit(metadata["Timer unit"].str.split(" ").first()).alias("timer_unit")
    total_time_col = (
        pl.lit(metadata["Total time"].str.split(" ").explode().first())
        .cast(pl.Float64)
        .alias("total_time")
    )
    source_file_col = pl.lit(metadata["File"].first()).alias("source_file")
    function_col = pl.lit(metadata["Function"].first()).alias("function")
    merged = parsed_data.with_columns(
        timer_unit=tu_col,
        total_time=total_time_col,
        source_file=source_file_col,
        function=function_col,
    )
    if merge_metadata:
        return merged
    else:
        lines = merged.filter(pl.col("line_contents").is_not_null()).drop(
            "total_time", "source_file", "function", "timer_unit"
        )
        return metadata, lines
