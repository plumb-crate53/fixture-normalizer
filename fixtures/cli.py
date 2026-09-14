"""Command-line entry point: read messy fixture lines, print normalised ones."""

from __future__ import annotations

import argparse
import sys

from .formatter import FixtureFormatError, parse_fixture


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalise messy sports fixture lines.")
    parser.add_argument(
        "path",
        nargs="?",
        help="file with one fixture per line; reads stdin if omitted",
    )
    args = parser.parse_args(argv)

    lines = _read_lines(args.path)

    exit_code = 0
    for line in lines:
        if not line.strip():
            continue
        try:
            fixture = parse_fixture(line)
        except FixtureFormatError as exc:
            print(f"skip: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(fixture.to_string())
    return exit_code


def _read_lines(path: str | None) -> list[str]:
    if path is None:
        return sys.stdin.readlines()
    with open(path, encoding="utf-8") as handle:
        return handle.readlines()


if __name__ == "__main__":
    raise SystemExit(main())
