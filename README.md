# fixture-normalizer

Fixture lists collected from different sources never agree on format. One
site writes "Man Utd vs Chelsea, 12/09/2026 3pm", another writes "arsenal v
spurs - Sept 12 2026 15:00", and a spreadsheet export gives you
"Newcastle @ 2026-09-12 3:00pm West Ham". This is a small library that takes
that mess and turns it into a consistent structure: two canonical team
names, a `date`, and a `time`.

## Usage

```python
from fixtures import parse_fixture

fixture = parse_fixture("Man Utd vs Chelsea, 12/09/2026 3pm")
print(fixture.home)          # Manchester United
print(fixture.away)          # Chelsea
print(fixture.kickoff_date)  # 2026-09-12
print(fixture.kickoff_time)  # 15:00:00
print(fixture.to_string())   # Manchester United vs Chelsea — 2026-09-12 15:00
```

Lines that can't be parsed raise `FixtureFormatError` with a message
describing what went wrong. If you're processing a whole file and want to
skip bad lines instead of stopping, use `format_many`:

```python
from fixtures import format_many

lines = [
    "arsenal v spurs - Sept 12 2026 15:00",
    "this line has no separator so it gets skipped",
    "Newcastle @ West Ham, 2026-09-13 12:30pm",
]
for fixture in format_many(lines):
    print(fixture.to_csv_row())
```

There's also a small CLI:

```
python -m fixtures.cli fixtures.txt
```

It reads one fixture per line (or from stdin if no file is given) and
prints the normalised form, one per line, skipping anything it can't parse
and reporting those to stderr.

## What it currently handles

- Separators: `vs`, `v`, `@`, `at` (case-insensitive)
- Team names: known club nicknames (Man Utd, Spurs, Wolves, ...) are
  expanded to full names; anything else is just cleaned up and cased
- Dates: ISO (`2026-09-12`), day-month-year numeric (`12/09/2026`), and
  month-name forms in either order (`12 Sept 2026`, `September 12, 2026`)
- Times: `3pm`, `3:30pm`, `15:00`, `15.00`

Numeric dates are assumed to be day-first, matching how most fixture lists
outside the US are written. There's no reliable way to tell day-first from
month-first apart from context, so this is a documented assumption rather
than something the parser guesses at.

## Running the tests

```
python -m unittest discover
```

## Status

Early skeleton. The parsing rules cover the formats I've actually run into
so far, not every possible way of writing a date.
