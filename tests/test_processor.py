import json
import pickle
import unittest
from dataclasses import asdict
from datetime import datetime
from typing import List

from espn_api.basketball import League
from espn_api.basketball.box_score import H2HCategoryBoxScore as BoxScore

from processor import Processor


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

        # property assertions
        self.assertTrue(len(cat5_instance.teams) > 0)
        self.assertTrue(
            0 < len(cat5_instance.matchups) <= len(cat5_instance.teams) // 2
        )
        self.assertTrue(
            len(cat5_instance.players) > 8 * len(cat5_instance.teams)
        )
        ex_float = cat5_instance.matchups[0].forecasts.default.catWin['PTS']
        self.assertEqual(round(ex_float, 4), ex_float)

        for matchup in cat5_instance.matchups:
            for forecast in (matchup.forecasts.default, matchup.forecasts.homeOptimized,
                             matchup.forecasts.awayOptimized):
                self.assertEqual(9, len(forecast.catWin))
                self.assertEqual(set(forecast.catWin), set(forecast.catTie))
                for home, tie in [(forecast.win, forecast.tie), *[
                    (forecast.catWin[cat], forecast.catTie[cat]) for cat in forecast.catWin
                ]]:
                    self.assertTrue(0 <= home <= 1)
                    self.assertTrue(0 <= tie <= 1)
                    self.assertLessEqual(home + tie, 1.0001)
                    self.assertEqual(round(home, 4), home)
                    self.assertEqual(round(tie, 4), tie)

            self.assertGreaterEqual(matchup.forecasts.homeOptimized.win,
                                    matchup.forecasts.default.win)
            away_opt = matchup.forecasts.awayOptimized
            default = matchup.forecasts.default
            self.assertGreaterEqual(1 - away_opt.win - away_opt.tie + .0001,
                                    1 - default.win - default.tie)

        # test json serialization
        cat5_instance_dict = asdict(cat5_instance)
        cat5_instance_json = json.dumps(cat5_instance_dict, indent=2)
        self.assertTrue(len(cat5_instance_json) > 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
