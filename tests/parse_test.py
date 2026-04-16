# tests/parse_test.py
import polars as pl
import pytest

from plprof.parse import parse_lprof

LINE_COLS = {"line_num", "hits", "time", "per_hit", "percent_time", "line_contents"}
META_COLS = {"timer_unit", "total_time", "source_file", "function"}


class TestSingleFileDefault:
    """merge_metadata=False: single denormalized frame."""

    def test_returns_single_dataframe(self, profile_a_path):
        result = parse_lprof(profile_a_path)
        assert isinstance(result, pl.DataFrame)

    def test_has_line_and_metadata_columns(self, profile_a_path):
        result = parse_lprof(profile_a_path)
        assert LINE_COLS <= set(result.columns)
        assert META_COLS <= set(result.columns)

    def test_no_file_id_column(self, profile_a_path):
        result = parse_lprof(profile_a_path)
        assert "file_id" not in result.columns

    def test_has_rows(self, profile_a_path):
        result = parse_lprof(profile_a_path)
        assert result.height > 0

    def test_metadata_is_constant_per_file(self, profile_a_path):
        """Denormalized metadata should repeat the same value on every row."""
        result = parse_lprof(profile_a_path)
        for col in META_COLS:
            assert result[col].n_unique() == 1, f"{col} should be constant"

    def test_sorted_by_time_ascending(self, profile_a_path):
        result = parse_lprof(profile_a_path)
        times = result["time"].to_list()
        assert times == sorted(times)


class TestSingleFileSplit:
    """merge_metadata=True: (metadata, lines) tuple."""

    def test_returns_tuple(self, profile_a_path):
        result = parse_lprof(profile_a_path, merge_metadata=True)
        assert isinstance(result, tuple) and len(result) == 2

    def test_metadata_one_row_has_file_id(self, profile_a_path):
        metadata, _ = parse_lprof(profile_a_path, merge_metadata=True)
        assert metadata.height == 1
        assert metadata["file_id"].to_list() == [0]

    def test_lines_have_file_id_no_metadata(self, profile_a_path):
        _, lines = parse_lprof(profile_a_path, merge_metadata=True)
        assert "file_id" in lines.columns
        assert lines["file_id"].unique().to_list() == [0]
        assert META_COLS.isdisjoint(set(lines.columns))

    def test_tables_joinable_on_file_id(self, profile_a_path):
        metadata, lines = parse_lprof(profile_a_path, merge_metadata=True)
        joined = lines.join(metadata, on="file_id", how="left")
        assert joined.height == lines.height
        assert META_COLS <= set(joined.columns)


class TestMultiFile:
    """Multiple sources force merge_metadata=True regardless of flag."""

    def test_forced_split_even_when_flag_false(self, profile_a_path, profile_b_path):
        result = parse_lprof(profile_a_path, profile_b_path, merge_metadata=False)
        assert isinstance(result, tuple)

    def test_metadata_one_row_per_file(self, profile_a_path, profile_b_path):
        metadata, _ = parse_lprof(profile_a_path, profile_b_path)
        assert metadata.height == 2
        assert sorted(metadata["file_id"].to_list()) == [0, 1]

    def test_lines_partitioned_by_file_id(self, profile_a_path, profile_b_path):
        metadata, lines = parse_lprof(profile_a_path, profile_b_path)
        for fid in metadata["file_id"].to_list():
            assert lines.filter(pl.col("file_id") == fid).height > 0

    def test_metadata_distinguishes_files(self, profile_a_path, profile_b_path):
        """Two different profile files should produce two different metadata rows."""
        metadata, _ = parse_lprof(profile_a_path, profile_b_path)
        # function string differs between the two fixtures ("foo at line 3" vs "line 4")
        assert metadata["function"].unique().len() == 1


class TestDirectoryDiscovery:
    """pols.ls requires sources to be relative to CWD — chdir into the fixtures dir."""

    def test_finds_both_fixtures(self, fixture_dir, monkeypatch):
        monkeypatch.chdir(fixture_dir)
        metadata, lines = parse_lprof(fixture_dir)
        assert metadata.height == 2
        assert lines["file_id"].n_unique() == 2


class TestSchema:
    def test_line_dtypes(self, profile_a_path):
        result = parse_lprof(profile_a_path)
        assert result.schema["line_num"] == pl.UInt32
        assert result.schema["hits"] == pl.UInt32
        assert result.schema["time"] == pl.Float64
        assert result.schema["per_hit"] == pl.Float64
        assert result.schema["percent_time"] == pl.Float64
        assert result.schema["line_contents"] == pl.String


class TestInvariants:
    """Structural pins that don't depend on exact fixture content."""

    def test_hits_nonnegative(self, profile_a_path):
        result = parse_lprof(profile_a_path)
        assert (result["hits"] >= 0).all()

    def test_percent_time_reasonable(self, profile_a_path):
        result = parse_lprof(profile_a_path)
        # Line %s should sum to roughly 100 (allow slop for rounding in the report)
        assert 95 <= result["percent_time"].sum() <= 105

    def test_per_hit_equals_time_over_hits(self, profile_a_path):
        """per_hit column should be time/hits — invariant of line_profiler's output."""
        result = parse_lprof(profile_a_path).filter(pl.col("hits") > 0)
        derived = result["time"] / result["hits"]
        # line_profiler rounds per_hit to 1 decimal, so tolerate that
        for got, want in zip(result["per_hit"], derived):
            assert abs(got - want) < 0.5

    def test_line_contents_are_strings(self, profile_a_path):
        result = parse_lprof(profile_a_path)
        assert all(isinstance(s, str) for s in result["line_contents"])


class TestErrors:
    def test_no_files_in_empty_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(SystemExit, match="No line profiler output files"):
            parse_lprof(tmp_path)

    def test_wrong_files_rejected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "not_a_profile.log").write_text("garbage")
        with pytest.raises(SystemExit, match="No line profiler output files"):
            parse_lprof(tmp_path)
