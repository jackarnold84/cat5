import unittest
from typing import List, Tuple
from unittest.mock import MagicMock

import numpy as np
from espn_api.basketball.box_score import H2HCategoryBoxScore as BoxScore

from cat5 import Model, PlayerStart
from cat5.model import skellam_cdf_approx, skellam_cdf_continuous


def sim_count_cat(
    home_curr: int,
    away_curr: int,
    home_proj: List[int],
    away_proj: List[int],
):
    res = []
    n = 50_000
    for _ in range(n):
        h = home_curr + sum(
            [np.random.poisson(x) for x in home_proj]
        )
        a = away_curr + sum(
            [np.random.poisson(x) for x in away_proj]
        )
        if h > a:
            res.append(1)
        elif h < a:
            res.append(0)
        else:
            res.append(np.random.choice([0, 1]))
    return np.mean(res)


def sim_ratio_cat(
    home_curr: Tuple[int, int],
    away_curr: Tuple[int, int],
    home_proj: List[Tuple[int, float]],
    away_proj: List[Tuple[int, float]],
):
    res = []
    n = 50_000
    for _ in range(n):
        h_make, h_att = home_curr
        for proj_att, proj_ratio in home_proj:
            att = np.random.poisson(proj_att)
            h_att += att
            h_make += np.random.binomial(att, proj_ratio)

        a_make, a_att = away_curr
        for proj_att, proj_ratio in away_proj:
            att = np.random.poisson(proj_att)
            a_att += att
            a_make += np.random.binomial(att, proj_ratio)

        if h_make / h_att > a_make / a_att:
            res.append(1)
        elif h_make / h_att < a_make / a_att:
            res.append(0)
        else:
            res.append(np.random.choice([0, 1]))
    return np.mean(res)


class TestModel(unittest.TestCase):
    def setUp(self):
        print('--> running')

    def test_predict_count_cat(self):
        # test case data
        home_curr = 100
        away_curr = 80
        home_proj = [10, 8, 7]
        away_proj = [8, 10, 6, 6, 10]

        # set up mocks
        box = MagicMock(spec=BoxScore)
        box.home_stats = {'PTS': {'value': home_curr}}
        box.away_stats = {'PTS': {'value': away_curr}}

        home_starts = []
        for proj in home_proj:
            player_start = MagicMock(spec=PlayerStart)
            player_start.projection.return_value = proj
            home_starts.append(player_start)
        away_starts = []
        for proj in away_proj:
            player_start = MagicMock(spec=PlayerStart)
            player_start.projection.return_value = proj
            away_starts.append(player_start)

        # test implementation
        cat_predict = Model(box, home_starts, away_starts)
        result = cat_predict._predict_count_cat('PTS')

        # sim expected
        exp_sim = sim_count_cat(home_curr, away_curr, home_proj, away_proj)

        # compare
        print(f'expected: {exp_sim:.2f}, got: {result:.2f}')
        self.assertAlmostEqual(result, exp_sim, delta=0.01)

    def test_predict_ratio_cat(self):
        # test case data
        home_curr = (29, 53)
        away_curr = (9, 30)
        home_proj = [(20.1, 0.442), (11.3, 0.617), (17.5, 0.440),
                     (14.4, 0.478), (17.4, 0.494)]
        away_proj = [(16.4, 0.450), (15.7, 0.492), (20.8, 0.610)]

        # set up mocks
        box = MagicMock(spec=BoxScore)
        box.home_stats = {'FGM': {'value': home_curr[0]},
                          'FGA': {'value': home_curr[1]}}
        box.away_stats = {'FGM': {'value': away_curr[0]},
                          'FGA': {'value': away_curr[1]}}

        def mock_proj(proj_att, proj_ratio):
            return lambda cat: proj_att if cat == 'FGA' else proj_ratio

        home_starts = []
        for proj_att, proj_ratio in home_proj:
            player_start = MagicMock(spec=PlayerStart)
            player_start.projection.side_effect = (
                mock_proj(proj_att, proj_ratio)
            )
            home_starts.append(player_start)
        away_starts = []
        for proj_att, proj_ratio in away_proj:
            player_start = MagicMock(spec=PlayerStart)
            player_start.projection.side_effect = (
                mock_proj(proj_att, proj_ratio)
            )
            away_starts.append(player_start)

        # test implementation
        cat_predict = Model(box, home_starts, away_starts)
        result = cat_predict._predict_ratio_cat('FG%')

        # sim expected
        exp_sim = sim_ratio_cat(home_curr, away_curr, home_proj, away_proj)

        # compare
        print(f'expected: {exp_sim:.2f}, got: {result:.2f}')
        self.assertAlmostEqual(result, exp_sim, delta=0.01)

    def test_predict_win(self):
        # set up mocks
        box = MagicMock(spec=BoxScore)
        cat_predict = Model(box, [], [])
        cat_predict.predict_cat = MagicMock(return_value=0.4)

        # test implementation
        result = cat_predict.predict_win()

        # compare
        expected_value = 0.27
        print(f'expected: {expected_value:.2f}, got: {result:.2f}')
        self.assertAlmostEqual(result, expected_value, delta=0.01)

    def test_skellam_cdf_approx(self):
        k = 3
        mu1 = 10
        mu2 = 12
        expected = skellam_cdf_continuous(k, mu1, mu2)
        result = skellam_cdf_approx(k, mu1, mu2)
        print(f'expected: {expected:.2f}, got: {result:.2f}')
        self.assertAlmostEqual(result, expected, delta=0.01)


if __name__ == '__main__':
    unittest.main(verbosity=2)
