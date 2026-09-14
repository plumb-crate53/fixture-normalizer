"""Canonical team names for clubs that show up under many spellings."""

_ALIASES = {
    "man utd": "Manchester United",
    "man u": "Manchester United",
    "manchester utd": "Manchester United",
    "man city": "Manchester City",
    "spurs": "Tottenham Hotspur",
    "tottenham": "Tottenham Hotspur",
    "wolves": "Wolverhampton Wanderers",
    "forest": "Nottingham Forest",
    "nottm forest": "Nottingham Forest",
    "brighton": "Brighton & Hove Albion",
    "west brom": "West Bromwich Albion",
    "west ham": "West Ham United",
    "newcastle": "Newcastle United",
    "leeds": "Leeds United",
    "sheff utd": "Sheffield United",
    "sheff wed": "Sheffield Wednesday",
    "qpr": "Queens Park Rangers",
}


def normalize_team_name(raw: str) -> str:
    """Collapse whitespace, fix casing, and expand known nicknames."""
    cleaned = " ".join(raw.split())
    if not cleaned:
        return ""
    key = cleaned.lower().strip(".")
    if key in _ALIASES:
        return _ALIASES[key]
    return _title_case(cleaned)


def _title_case(name: str) -> str:
    # str.title() mangles things like "AFC" or turns "O'Malley" into
    # "O'malley", so capitalise word-by-word and leave short all-caps
    # tokens (AFC, FC, US) as they are.
    words = []
    for word in name.split(" "):
        if word.isupper() and len(word) <= 3:
            words.append(word)
        elif word:
            words.append(word[:1].upper() + word[1:].lower())
        else:
            words.append(word)
    return " ".join(words)
