"""Turn messy, human-typed fixture lines into a consistent structure.

Fixture lists pulled from emails, forum posts, or copy-pasted spreadsheets
mix separators ("vs", "v", "@"), date orders, and time formats freely. This
module picks the pieces apart and normalises them without needing to know
the source format ahead of time.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, time

from .aliases import normalize_team_name

MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

_SEPARATORS = re.compile(r"\s+(?:vs\.?|v\.?|@|at)\s+", re.IGNORECASE)
_TEAM_BREAK = re.compile(r",|\s[-—]\s")

_DATE_PATTERNS = [
    re.compile(r"(?P<y>\d{4})-(?P<m>\d{1,2})-(?P<d>\d{1,2})"),
    re.compile(
        r"(?P<d>\d{1,2})(?:st|nd|rd|th)?\s+(?P<mon>[A-Za-z]+)\.?,?\s+(?P<y>\d{2,4})"
    ),
    re.compile(
        r"(?P<mon>[A-Za-z]+)\.?\s+(?P<d>\d{1,2})(?:st|nd|rd|th)?,?\s+(?P<y>\d{2,4})"
    ),
    # Day-first numeric, e.g. 12/09/2026 - matches how UK fixture lists
    # are usually written. There's no way to tell this apart from
    # month-first input, so that's a documented assumption, not a bug.
    re.compile(r"(?P<d>\d{1,2})[/.](?P<m>\d{1,2})[/.](?P<y>\d{2,4})"),
]

_TIME_PATTERN = re.compile(
    r"(?P<h>\d{1,2})(?:[:.](?P<min>\d{2}))?\s*(?P<ampm>am|pm)?", re.IGNORECASE
)


class FixtureFormatError(ValueError):
    """Raised when a fixture line can't be parsed with any known pattern."""


@dataclass(frozen=True)
class Fixture:
    home: str
    away: str
    kickoff_date: date | None
    kickoff_time: time | None

    def to_string(self) -> str:
        parts = [f"{self.home} vs {self.away}"]
        if self.kickoff_date is not None:
            parts.append(self.kickoff_date.isoformat())
        if self.kickoff_time is not None:
            parts.append(self.kickoff_time.strftime("%H:%M"))
        return " — ".join(parts)

    def to_csv_row(self) -> tuple[str, str, str, str]:
        return (
            self.home,
            self.away,
            self.kickoff_date.isoformat() if self.kickoff_date else "",
            self.kickoff_time.strftime("%H:%M") if self.kickoff_time else "",
        )


def _resolve_year(year: int) -> int:
    if year < 100:
        # Fixture lists rarely span a century, so two-digit years are
        # assumed to be 2000s. Fine until this is still running in 2099.
        return 2000 + year
    return year


def _parse_date(text: str) -> date | None:
    for pattern in _DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        groups = match.groupdict()
        year = _resolve_year(int(groups["y"]))
        if groups.get("mon"):
            month = MONTHS.get(groups["mon"].strip(".").lower())
            if month is None:
                continue
        else:
            month = int(groups["m"])
        day = int(groups["d"])
        try:
            return date(year, month, day)
        except ValueError:
            continue
    return None


def _parse_time(text: str) -> time | None:
    for match in _TIME_PATTERN.finditer(text):
        ampm = match.group("ampm")
        minute_raw = match.group("min")
        # A bare number with no colon and no am/pm is too ambiguous to be
        # a kickoff time - it's more likely a date fragment or a score.
        if ampm is None and minute_raw is None:
            continue
        hour = int(match.group("h"))
        minute = int(minute_raw) if minute_raw else 0
        if ampm and ampm.lower() == "pm" and hour != 12:
            hour += 12
        if ampm and ampm.lower() == "am" and hour == 12:
            hour = 0
        if 0 <= hour < 24 and 0 <= minute < 60:
            return time(hour, minute)
    return None


def _find_away_team_end(rest: str) -> int | None:
    """Find where the away team name stops and the date/time starts."""
    positions = []
    break_match = _TEAM_BREAK.search(rest)
    if break_match:
        positions.append(break_match.start())
    for pattern in _DATE_PATTERNS:
        date_match = pattern.search(rest)
        if date_match:
            positions.append(date_match.start())
    return min(positions) if positions else None


def parse_fixture(line: str) -> Fixture:
    """Parse one messy fixture line into a Fixture.

    Raises FixtureFormatError if no team separator can be found or if a
    team name can't be extracted from either side of it.
    """
    line = line.strip()
    if not line:
        raise FixtureFormatError("empty line")

    separator = _SEPARATORS.search(line)
    if not separator:
        raise FixtureFormatError(f"no 'vs'/'v'/'@' separator found in: {line!r}")

    home_raw = line[: separator.start()]
    rest = line[separator.end() :]

    end = _find_away_team_end(rest)
    away_raw = rest[:end] if end is not None else rest

    home = normalize_team_name(home_raw)
    away = normalize_team_name(away_raw)
    if not home or not away:
        raise FixtureFormatError(f"could not extract both team names from: {line!r}")

    return Fixture(
        home=home,
        away=away,
        kickoff_date=_parse_date(rest),
        kickoff_time=_parse_time(rest),
    )


def format_many(lines: list[str]) -> list[Fixture]:
    """Parse every line, skipping ones that fail rather than aborting the batch."""
    fixtures = []
    for line in lines:
        if not line.strip():
            continue
        try:
            fixtures.append(parse_fixture(line))
        except FixtureFormatError:
            continue
    return fixtures
