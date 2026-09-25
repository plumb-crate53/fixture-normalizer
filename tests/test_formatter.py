from __future__ import annotations

import unittest
from datetime import date, time

from fixtures import Fixture, FixtureFormatError, format_many, parse_fixture
from fixtures.formatter import _parse_date, _parse_time


class SeparatorTests(unittest.TestCase):
    def test_vs_lowercase(self):
        f = parse_fixture("Arsenal vs Chelsea")
        self.assertEqual((f.home, f.away), ("Arsenal", "Chelsea"))

    def test_v_single_letter(self):
        f = parse_fixture("Arsenal v Chelsea")
        self.assertEqual((f.home, f.away), ("Arsenal", "Chelsea"))

    def test_at_sign(self):
        f = parse_fixture("Arsenal @ Chelsea")
        self.assertEqual((f.home, f.away), ("Arsenal", "Chelsea"))

    def test_at_word(self):
        f = parse_fixture("Arsenal at Chelsea")
        self.assertEqual((f.home, f.away), ("Arsenal", "Chelsea"))

    def test_separator_is_case_insensitive(self):
        f = parse_fixture("Arsenal VS Chelsea")
        self.assertEqual((f.home, f.away), ("Arsenal", "Chelsea"))

    def test_v_with_trailing_dot(self):
        f = parse_fixture("Arsenal v. Chelsea")
        self.assertEqual((f.home, f.away), ("Arsenal", "Chelsea"))

    def test_separator_does_not_match_inside_a_word(self):
        # "Watford" contains the letters "at" but not as a standalone word,
        # so it must not be mistaken for the "at" separator.
        f = parse_fixture("Watford vs Bournemouth")
        self.assertEqual((f.home, f.away), ("Watford", "Bournemouth"))

    def test_no_separator_raises(self):
        with self.assertRaises(FixtureFormatError):
            parse_fixture("Arsenal Chelsea, 2026-09-12 15:00")

    def test_empty_line_raises(self):
        with self.assertRaises(FixtureFormatError):
            parse_fixture("   ")


class DateParsingTests(unittest.TestCase):
    def test_iso(self):
        self.assertEqual(_parse_date("2026-09-12"), date(2026, 9, 12))

    def test_day_first_numeric_slash(self):
        self.assertEqual(_parse_date("12/09/2026"), date(2026, 9, 12))

    def test_day_first_numeric_dot(self):
        self.assertEqual(_parse_date("12.09.2026"), date(2026, 9, 12))

    def test_two_digit_year_is_assumed_2000s(self):
        self.assertEqual(_parse_date("12/09/26"), date(2026, 9, 12))

    def test_day_month_name_year(self):
        self.assertEqual(_parse_date("12 Sept 2026"), date(2026, 9, 12))

    def test_day_with_ordinal_suffix(self):
        self.assertEqual(_parse_date("12th September 2026"), date(2026, 9, 12))

    def test_month_name_day_year(self):
        self.assertEqual(_parse_date("September 12, 2026"), date(2026, 9, 12))

    def test_month_name_day_year_abbreviated(self):
        self.assertEqual(_parse_date("Sept 12 2026"), date(2026, 9, 12))

    def test_invalid_calendar_date_returns_none(self):
        # 31 Feb doesn't exist in any year; no other pattern matches either.
        self.assertIsNone(_parse_date("31/02/2026"))

    def test_unknown_month_name_returns_none(self):
        self.assertIsNone(_parse_date("12 Frobruary 2026"))

    def test_no_date_returns_none(self):
        self.assertIsNone(_parse_date("no date here"))

    def test_month_first_flag_swaps_numeric_slash_date(self):
        self.assertEqual(
            _parse_date("09/12/2026", month_first=True), date(2026, 9, 12)
        )

    def test_month_first_flag_swaps_numeric_dot_date(self):
        self.assertEqual(
            _parse_date("09.12.2026", month_first=True), date(2026, 9, 12)
        )

    def test_month_first_flag_does_not_affect_iso_date(self):
        self.assertEqual(
            _parse_date("2026-09-12", month_first=True), date(2026, 9, 12)
        )

    def test_month_first_flag_does_not_affect_month_name_date(self):
        self.assertEqual(
            _parse_date("12 Sept 2026", month_first=True), date(2026, 9, 12)
        )

    def test_month_first_flag_invalid_calendar_date_returns_none(self):
        # With month_first, "13/09/2026" would need a 13th month, so no
        # pattern produces a valid date and this falls through to None.
        self.assertIsNone(_parse_date("13/09/2026", month_first=True))


class TimeParsingTests(unittest.TestCase):
    def test_hour_with_pm(self):
        self.assertEqual(_parse_time("3pm"), time(15, 0))

    def test_hour_with_am(self):
        self.assertEqual(_parse_time("3am"), time(3, 0))

    def test_noon(self):
        self.assertEqual(_parse_time("12pm"), time(12, 0))

    def test_midnight(self):
        self.assertEqual(_parse_time("12am"), time(0, 0))

    def test_hour_minute_with_colon_and_pm(self):
        self.assertEqual(_parse_time("3:30pm"), time(15, 30))

    def test_24h_with_colon(self):
        self.assertEqual(_parse_time("15:00"), time(15, 0))

    def test_24h_with_dot(self):
        self.assertEqual(_parse_time("15.00"), time(15, 0))

    def test_bare_number_is_too_ambiguous(self):
        # No colon and no am/pm - could be a date fragment, so it's skipped.
        self.assertIsNone(_parse_time("12"))

    def test_out_of_range_hour_is_skipped(self):
        self.assertIsNone(_parse_time("25:00"))

    def test_out_of_range_minute_is_skipped(self):
        self.assertIsNone(_parse_time("3:75pm"))

    def test_no_time_returns_none(self):
        self.assertIsNone(_parse_time("no time here"))


class FixtureIntegrationTests(unittest.TestCase):
    def test_readme_example_slash_date(self):
        f = parse_fixture("Man Utd vs Chelsea, 12/09/2026 3pm")
        self.assertEqual(f.home, "Manchester United")
        self.assertEqual(f.away, "Chelsea")
        self.assertEqual(f.kickoff_date, date(2026, 9, 12))
        self.assertEqual(f.kickoff_time, time(15, 0))

    def test_readme_example_dash_and_month_name(self):
        f = parse_fixture("arsenal v spurs - Sept 12 2026 15:00")
        self.assertEqual(f.home, "Arsenal")
        self.assertEqual(f.away, "Tottenham Hotspur")
        self.assertEqual(f.kickoff_date, date(2026, 9, 12))
        self.assertEqual(f.kickoff_time, time(15, 0))

    def test_readme_example_at_sign_and_iso_date(self):
        f = parse_fixture("Newcastle @ West Ham, 2026-09-13 12:30pm")
        self.assertEqual(f.home, "Newcastle United")
        self.assertEqual(f.away, "West Ham United")
        self.assertEqual(f.kickoff_date, date(2026, 9, 13))
        self.assertEqual(f.kickoff_time, time(12, 30))

    def test_missing_date_does_not_prevent_parsing(self):
        f = parse_fixture("Arsenal vs Chelsea 31/02/2026")
        self.assertEqual((f.home, f.away), ("Arsenal", "Chelsea"))
        self.assertIsNone(f.kickoff_date)

    def test_to_string_omits_missing_parts(self):
        f = Fixture(home="Arsenal", away="Chelsea", kickoff_date=None, kickoff_time=None)
        self.assertEqual(f.to_string(), "Arsenal vs Chelsea")

    def test_month_first_flag_on_full_fixture_line(self):
        f = parse_fixture("Arsenal vs Chelsea, 09/12/2026 3pm", month_first=True)
        self.assertEqual(f.kickoff_date, date(2026, 9, 12))

    def test_month_first_flag_defaults_to_day_first(self):
        f = parse_fixture("Arsenal vs Chelsea, 09/12/2026 3pm")
        self.assertEqual(f.kickoff_date, date(2026, 12, 9))

    def test_to_csv_row(self):
        f = parse_fixture("Man Utd vs Chelsea, 12/09/2026 3pm")
        self.assertEqual(
            f.to_csv_row(),
            ("Manchester United", "Chelsea", "2026-09-12", "15:00"),
        )


class FormatManyTests(unittest.TestCase):
    def test_skips_unparseable_lines(self):
        lines = [
            "arsenal v spurs - Sept 12 2026 15:00",
            "this line has no separator so it gets skipped",
            "",
            "Newcastle @ West Ham, 2026-09-13 12:30pm",
        ]
        fixtures = format_many(lines)
        self.assertEqual(len(fixtures), 2)
        self.assertEqual(fixtures[0].away, "Tottenham Hotspur")
        self.assertEqual(fixtures[1].home, "Newcastle United")

    def test_month_first_flag_is_passed_through(self):
        fixtures = format_many(
            ["Arsenal vs Chelsea, 09/12/2026 3pm"], month_first=True
        )
        self.assertEqual(fixtures[0].kickoff_date, date(2026, 9, 12))


if __name__ == "__main__":
    unittest.main()
