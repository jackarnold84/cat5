import json
import pickle
import unittest
from dataclasses import asdict
from datetime import datetime
from typing import List

from espn_api.basketball import League
from espn_api.basketball.box_score import H2HCategoryBoxScore as BoxScore

from processor import Processor
from processor.utils import CustomEncoder


class TestModel(unittest.TestCase):
    def setUp(self) -> None:
        print('--> running')

        with open('tests/pickles/league_20250109.pkl', 'rb') as file:
            self.league: League = pickle.load(file)

        with open('tests/pickles/box_scores_20250109.pkl', 'rb') as file:
            self.box_scores: List[BoxScore] = pickle.load(file)

    def test_processor(self):
        processor = Processor(self.league, self.box_scores)
        processor.now = datetime(2025, 1, 9)
        processor.n_iter = 100
        cat5_instance = processor.build()

        self.assertTrue(len(cat5_instance.teams) > 0)
        self.assertTrue(
            0 < len(cat5_instance.matchups) <= len(cat5_instance.teams) // 2
        )
        self.assertTrue(
            len(cat5_instance.players) > 8 * len(cat5_instance.teams)
        )

        for matchup in cat5_instance.matchups:
            self.assertEqual(9, len(matchup.forecasts.default.catWin))
            self.assertTrue(0 <= matchup.forecasts.default.win <= 1)
            for p in matchup.forecasts.default.catWin.values():
                self.assertTrue(0 <= p <= 1)

            self.assertGreaterEqual(
                matchup.forecasts.homeOptimized.win,
                matchup.forecasts.default.win,
            )
            self.assertLessEqual(
                matchup.forecasts.awayOptimized.win,
                matchup.forecasts.default.win,
            )

        cat5_instance_dict = asdict(cat5_instance)
        cat5_instance_json = json.dumps(
            cat5_instance_dict,
            cls=CustomEncoder,
            indent=2,
        )
        self.assertTrue(len(cat5_instance_json) > 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
