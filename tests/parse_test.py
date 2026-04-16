import polars as pl

from plprof.parse import parse_lprof


def test_single_file(profile_a_path):
    df = parse_lprof(profile_a_path)

    assert isinstance(df, pl.DataFrame)
    assert df.height > 0

    # Should include metadata columns in single-file mode
    for col in ["timer_unit", "total_time", "source_file", "function"]:
        assert col in df.columns


def test_multi_file_returns_split(profile_a_path, profile_b_path):
    metadata, lines = parse_lprof(profile_a_path, profile_b_path)

    assert isinstance(metadata, pl.DataFrame)
    assert isinstance(lines, pl.DataFrame)

    # Metadata should have one row per file
    assert metadata.height == 2

    # Lines should include file_id
    assert "file_id" in lines.columns

    # Metadata should include file_id
    assert "file_id" in metadata.columns


def test_join_roundtrip(profile_a_path, profile_b_path):
    metadata, lines = parse_lprof(profile_a_path, profile_b_path)

    joined = lines.join(metadata, on="file_id", how="left")

    # After join, metadata columns should be present
    for col in ["total_time", "source_file", "function"]:
        assert col in joined.columns

    # Row count should not change
    assert joined.height == lines.height
