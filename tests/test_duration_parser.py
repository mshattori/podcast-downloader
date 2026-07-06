import pytest
from podcast_downloader.core.duration_parser import format_duration, parse_duration


class TestParseDuration:
    def test_seconds_only(self):
        assert parse_duration("3600") == 3600

    def test_mm_ss(self):
        assert parse_duration("60:00") == 3600

    def test_hh_mm_ss(self):
        assert parse_duration("1:00:00") == 3600

    def test_mm_ss_over_60_minutes(self):
        assert parse_duration("90:30") == 5430

    def test_zero_seconds(self):
        assert parse_duration("0") == 0

    def test_none_input(self):
        assert parse_duration(None) is None

    def test_empty_string(self):
        assert parse_duration("") is None

    def test_whitespace_string(self):
        assert parse_duration("   ") is None

    def test_invalid_format(self):
        assert parse_duration("abc") is None
        assert parse_duration("1:2:3:4") is None
        assert parse_duration("1:xx") is None

    def test_large_value(self):
        assert parse_duration("99:59:59") == 359999

    def test_hh_mm_ss_with_leading_zeros(self):
        assert parse_duration("01:30:00") == 5400

    def test_non_string_input(self):
        assert parse_duration(3600) is None  # type: ignore[arg-type]


class TestFormatDuration:
    def test_none(self):
        assert format_duration(None) == "不明"

    def test_seconds_only(self):
        assert format_duration(45) == "45秒"

    def test_zero(self):
        assert format_duration(0) == "0秒"

    def test_exactly_one_minute(self):
        assert format_duration(60) == "1分00秒"

    def test_minutes_and_seconds(self):
        assert format_duration(2730) == "45分30秒"

    def test_exactly_one_hour(self):
        assert format_duration(3600) == "1時間00分00秒"

    def test_hours_minutes_seconds(self):
        assert format_duration(5400) == "1時間30分00秒"

    def test_negative_value_treated_as_zero(self):
        assert format_duration(-1) == "0秒"

    def test_roundtrip_with_parse(self):
        for raw, expected_secs in [("1:30:00", 5400), ("45:30", 2730), ("3600", 3600)]:
            secs = parse_duration(raw)
            assert secs == expected_secs
            assert format_duration(secs) != "不明"
