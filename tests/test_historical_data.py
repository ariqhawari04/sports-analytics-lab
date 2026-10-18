
import pandas as pd

from src.processing.backfill_historical import (
    TEAM_ALIASES,
    NEW_SEASONS,
    normalize_team_names,
)


# Check historical season coverage
assert len(NEW_SEASONS) == 9
assert NEW_SEASONS[0] == "2015-16"
assert NEW_SEASONS[-1] == "2023-24"

# Every configured historical alias must be
# converted into its canonical club name.
sample = pd.DataFrame({
    "home_team": list(TEAM_ALIASES.keys()),
    "away_team": list(TEAM_ALIASES.values()),
})

normalized = normalize_team_names(sample)

assert normalized["home_team"].tolist() == (
    list(TEAM_ALIASES.values())
)

assert normalized["away_team"].tolist() == (
    list(TEAM_ALIASES.values())
)

# Normalization must be idempotent:
# running it twice should change nothing.
normalized_twice = normalize_team_names(normalized)

assert normalized.equals(normalized_twice)

# Explicit cross-season identity check
example = pd.DataFrame({
    "home_team": [
        "Manchester United",
        "Manchester United FC",
    ],
    "away_team": [
        "Leicester City",
        "Leicester City FC",
    ],
})

cleaned = normalize_team_names(example)

assert cleaned["home_team"].nunique() == 1
assert cleaned["away_team"].nunique() == 1

print("Historical team normalization passed!")
