
"""
SAL v0.3 — Multi-League Regression Tests

Offline tests: no API calls or database writes.
Optional historical CSV checks run when the
local preview dataset is available.
"""

import unittest
from pathlib import Path

import pandas as pd

from src.analysis.match_results import build_team_results
from src.analysis.standings import build_standings
from src.analysis.head_to_head import get_head_to_head


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = (
    ROOT / "data" / "processed"
    / "multi_league_historical_preview.csv"
)


def fixture(league, season, date, home, away, hg, ag):
    return {
        "league_code": league,
        "season": season,
        "match_date": date,
        "matchweek": 1,
        "home_team": home,
        "away_team": away,
        "home_goals": hg,
        "away_goals": ag,
    }


class MultiLeagueTests(unittest.TestCase):

    def setUp(self):
        self.matches = pd.DataFrame([
            fixture(
                "PL", "2024-25", "2024-08-10",
                "Manchester United FC", "Arsenal FC",
                2, 0,
            ),
            fixture(
                "PL", "2024-25", "2025-01-10",
                "Arsenal FC", "Manchester United FC",
                0, 0,
            ),
            fixture(
                "BL1", "2024-25", "2024-08-20",
                "FC Bayern München", "Bayer 04 Leverkusen",
                3, 1,
            ),
            fixture(
                "PD", "2023-24", "2023-09-10",
                "Real Madrid CF", "FC Barcelona",
                2, 1,
            ),
            fixture(
                "SA", "2023-24", "2023-09-15",
                "AC Milan", "AC Monza",
                1, 0,
            ),
            fixture(
                "FL1", "2023-24", "2023-09-20",
                "Paris Saint-Germain FC", "AS Monaco FC",
                2, 2,
            ),
        ])

    def selected(self, league, season):
        return self.matches.loc[
            (self.matches["league_code"] == league)
            & (self.matches["season"] == season)
        ].copy()

    def test_each_match_produces_two_team_results(self):
        results = build_team_results(self.matches)

        self.assertEqual(
            len(results),
            2 * len(self.matches),
        )

    def test_five_leagues_calculate_independently(self):
        cases = [
            ("PL", "2024-25", "Manchester United FC", 4),
            ("BL1", "2024-25", "FC Bayern München", 3),
            ("PD", "2023-24", "Real Madrid CF", 3),
            ("SA", "2023-24", "AC Milan", 3),
            ("FL1", "2023-24", "Paris Saint-Germain FC", 1),
        ]

        for league, season, club, expected in cases:
            with self.subTest(league=league):
                results = build_team_results(
                    self.selected(league, season)
                )

                table = build_standings(results)
                by_team = table.set_index("team")

                self.assertEqual(
                    int(by_team.loc[club, "Pts"]),
                    expected,
                )

    def test_home_and_away_results(self):
        results = build_team_results(
            self.selected("PL", "2024-25")
        )

        united = results.loc[
            results["team"] == "Manchester United FC"
        ]

        arsenal = results.loc[
            results["team"] == "Arsenal FC"
        ]

        self.assertEqual(
            united["result"].tolist(),
            ["W", "D"],
        )
        self.assertEqual(
            arsenal["result"].tolist(),
            ["L", "D"],
        )

    def test_cumulative_points(self):
        results = build_team_results(
            self.selected("PL", "2024-25")
        )

        united = results.loc[
            results["team"] == "Manchester United FC"
        ]

        self.assertEqual(
            united["cumulative_points"].tolist(),
            [3, 4],
        )
        self.assertEqual(
            united["match_number"].tolist(),
            [1, 2],
        )

    def test_mixed_leagues_are_rejected(self):
        results = build_team_results(
            self.matches.loc[
                self.matches["season"] == "2024-25"
            ]
        )

        with self.assertRaisesRegex(
            ValueError, "exactly one league"
        ):
            build_standings(results)

    def test_mixed_seasons_are_rejected(self):
        results = build_team_results(self.matches)

        with self.assertRaisesRegex(
            ValueError, "exactly one season"
        ):
            build_standings(results)

    def test_same_name_stays_isolated(self):
        # Synthetic clubs deliberately share a name
        # to detect cross-league aggregation errors.
        data = pd.DataFrame([
            fixture(
                "PL", "2024-25", "2024-08-01",
                "Shared FC", "PL Opponent", 2, 0,
            ),
            fixture(
                "BL1", "2024-25", "2024-08-02",
                "Shared FC", "BL Opponent", 0, 1,
            ),
        ])

        results = build_team_results(data)
        shared = results.loc[
            results["team"] == "Shared FC"
        ].set_index("league_code")

        self.assertEqual(
            int(shared.loc["PL", "cumulative_points"]), 3
        )
        self.assertEqual(
            int(shared.loc["BL1", "cumulative_points"]), 0
        )
        self.assertTrue(
            (shared["match_number"] == 1).all()
        )

    def test_deductions_apply_only_to_epl(self):
        base = {
            "season": "2023-24",
            "team": "Everton FC",
            "result": "W",
            "points": 3,
            "goals_for": 1,
            "goals_against": 0,
        }

        # The non-EPL example is deliberately synthetic.
        for league, expected_deduction in [
            ("PL", 8),
            ("SA", 0),
        ]:
            with self.subTest(league=league):
                row = {**base, "league_code": league}
                table = build_standings(
                    pd.DataFrame([row])
                )

                self.assertEqual(
                    int(table.iloc[0]["Deduction"]),
                    expected_deduction,
                )

    def test_missing_score_is_rejected(self):
        data = self.selected("SA", "2023-24")
        data.loc[data.index[0], "home_goals"] = None

        with self.assertRaises(ValueError):
            build_team_results(data)

    def test_head_to_head(self):
        data = self.selected("SA", "2023-24")

        summary, meetings = get_head_to_head(
            data, "AC Milan", "AC Monza"
        )

        self.assertEqual(summary["matches"], 1)
        self.assertEqual(summary["team_a_wins"], 1)
        self.assertEqual(summary["team_b_wins"], 0)
        self.assertEqual(len(meetings), 1)

    @unittest.skipUnless(
        CSV_PATH.exists(),
        "Local historical CSV not available",
    )
    def test_historical_csv(self):
        df = pd.read_csv(
            CSV_PATH, parse_dates=["match_date"]
        )

        expected = {
            ("2023-24", "BL1"): (306, 18, "Bayer 04 Leverkusen"),
            ("2023-24", "FL1"): (306, 18, "Paris Saint-Germain FC"),
            ("2023-24", "PD"): (380, 20, "Real Madrid CF"),
            ("2023-24", "SA"): (380, 20, "FC Internazionale Milano"),
            ("2024-25", "BL1"): (306, 18, "FC Bayern München"),
            ("2024-25", "FL1"): (306, 18, "Paris Saint-Germain FC"),
        }

        self.assertEqual(len(df), 1984)

        coverage = set(
            zip(df["season"], df["league_code"])
        )
        self.assertEqual(coverage, set(expected))

        for (season, league), (count, clubs, winner) in expected.items():
            with self.subTest(season=season, league=league):
                matches = df.loc[
                    (df["season"] == season)
                    & (df["league_code"] == league)
                ]

                self.assertEqual(len(matches), count)

                results = build_team_results(matches)
                table = build_standings(results)

                self.assertEqual(len(table), clubs)
                self.assertEqual(table.iloc[0]["team"], winner)
                self.assertTrue(
                    (table["MP"] == clubs * 2 - 2).all()
                )


if __name__ == "__main__":
    unittest.main()
