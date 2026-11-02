import unittest
from itertools import product
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
from scipy.stats import poisson, skellam

from cat5.model import Model, Outcome, scored_cats


def count_model(home, away, home_mu=0, away_mu=0, cat='PTS'):
    box = SimpleNamespace(home_stats={cat: {'value': home}},
                          away_stats={cat: {'value': away}})
    return Model(box, [SimpleNamespace(projection=lambda _: home_mu)],
                 [SimpleNamespace(projection=lambda _: away_mu)])


def ratio_model(home, away, home_proj=(), away_proj=()):
    box = SimpleNamespace(home_stats={'FGM': {'value': home[0]}, 'FGA': {'value': home[1]}},
                          away_stats={'FGM': {'value': away[0]}, 'FGA': {'value': away[1]}})

    def starts(projections):
        return [SimpleNamespace(projection=lambda cat, a=a, p=p: a if cat == 'FGA' else p)
                for a, p in projections]

    return Model(box, starts(home_proj), starts(away_proj))


class TestModel(unittest.TestCase):
    def assertOutcome(self, actual, expected):
        for p, q in zip(actual, expected):
            self.assertGreaterEqual(p, 0)
            self.assertLessEqual(p, 1)
            self.assertAlmostEqual(p, q)
        self.assertAlmostEqual(sum(actual), 1)

    def test_count_ties_are_not_split(self):
        result = count_model(2, 2, 1, 1).predict_cat_outcome('PTS')
        tie = skellam.pmf(0, 1, 1)
        self.assertOutcome(result, ((1 - tie) / 2, (1 - tie) / 2, tie))

    def test_count_matches_seeded_simulation(self):
        rng = np.random.default_rng(42)
        diff = 20 + rng.poisson(25, 200000) - rng.poisson(40, 200000)
        result = count_model(100, 80, 25, 40).predict_cat_outcome('PTS')
        for p, expected in zip(result, [np.mean(diff > 0), np.mean(diff < 0), np.mean(diff == 0)]):
            self.assertAlmostEqual(p, expected, delta=0.004)

    def test_settled_counts(self):
        for home, away, expected in [(0, 0, (0, 0, 1)), (4, 3, (1, 0, 0)), (2, 3, (0, 1, 0))]:
            with self.subTest(home=home, away=away):
                self.assertOutcome(count_model(
                    home, away).predict_cat_outcome('PTS'), expected)

    def test_one_sided_production(self):
        self.assertOutcome(count_model(0, 1, 2, 0).predict_cat_outcome('PTS'),
                           (poisson.sf(1, 2), poisson.pmf(0, 2), poisson.pmf(1, 2)))
        self.assertOutcome(count_model(1, 0, 0, 2).predict_cat_outcome('PTS'),
                           (poisson.pmf(0, 2), poisson.sf(1, 2), poisson.pmf(1, 2)))
        self.assertOutcome(count_model(
            3, 0, 2, 0).predict_cat_outcome('PTS'), (1, 0, 0))

    def test_turnovers_preserve_ties(self):
        normal = count_model(2, 3, 5, 6).predict_cat_outcome('PTS')
        result = count_model(2, 3, 5, 6, 'TO').predict_cat_outcome('TO')
        self.assertOutcome(result, (normal.away, normal.home, normal.tie))

    def test_swap_symmetry_and_extreme_counts(self):
        for home, away, hmu, amu in [(2, 7, 3, 9), (0, 1, 0, 2), (900, 0, 500, 500)]:
            result = count_model(
                home, away, hmu, amu).predict_cat_outcome('PTS')
            swapped = count_model(
                away, home, amu, hmu).predict_cat_outcome('PTS')
            self.assertOutcome(
                result, (swapped.away, swapped.home, swapped.tie))

    def test_settled_shooting(self):
        for home, away, expected in [((1, 3), (2, 6), (0, 0, 1)),
                                     ((0, 0), (0, 0), (0, 0, 1)),
                                     ((0, 0), (0, 3), (0, 0, 1)),
                                     ((0, 0), (1, 3), (0, 1, 0)),
                                     ((3, 4), (1, 2), (1, 0, 0))]:
            with self.subTest(home=home, away=away):
                self.assertOutcome(ratio_model(
                    home, away).predict_cat_outcome('FG%'), expected)

    def test_settled_free_throw_tie(self):
        model = ratio_model((1, 3), (2, 6))
        model.box.home_stats = {'FTM': {'value': 1}, 'FTA': {'value': 3}}
        model.box.away_stats = {'FTM': {'value': 2}, 'FTA': {'value': 6}}
        self.assertOutcome(model.predict_cat_outcome('FT%'), (0, 0, 1))

    def test_deterministic_future_shooting(self):
        self.assertOutcome(ratio_model(
            (0, 0), (1, 1), [(2, 1)]).predict_cat_outcome('FG%'), (0, 0, 1))

    def test_uncertain_shooting_approximation(self):
        model = ratio_model((29, 53), (9, 30),
                            [(20.1, .442), (11.3, .617), (17.5, .440),
                             (14.4, .478), (17.4, .494)],
                            [(16.4, .450), (15.7, .492), (20.8, .610)])
        result = model.predict_cat_outcome('FG%')
        self.assertAlmostEqual(result.home, .88, delta=.01)
        self.assertOutcome(result, (result.home, 1 - result.home, 0))

    def test_matchup_settled_scores(self):
        for home, away, ties, expected in [(4, 3, 2, (1, 0, 0)), (3, 4, 2, (0, 1, 0)),
                                           (4, 4, 1, (0, 0, 1)), (0, 0, 9, (0, 0, 1))]:
            model = Model(None, [], [])
            results = [Outcome(1, 0, 0)] * home + [Outcome(0, 1, 0)
                                                   ] * away + [Outcome(0, 0, 1)] * ties
            model.predict_cat_outcome = Mock(
                side_effect=dict(zip(scored_cats, results)).__getitem__)
            self.assertOutcome(model.predict_outcome(), expected)

    def test_matchup_matches_enumeration(self):
        probabilities = [
            Outcome(.3, .5, .2), Outcome(.6, .1, .3), Outcome(.2, .2, .6)]
        expected = [0.0, 0.0, 0.0]
        for choices in product(range(3), repeat=3):
            margin = sum((1, -1, 0)[choice] for choice in choices)
            p = np.prod([probabilities[i][choice]
                        for i, choice in enumerate(choices)])
            expected[0 if margin > 0 else 1 if margin < 0 else 2] += p
        model = Model(None, [], [])
        results = probabilities + [Outcome(0, 0, 1)] * 6
        model.predict_cat_outcome = Mock(
            side_effect=dict(zip(scored_cats, results)).__getitem__)
        self.assertOutcome(model.predict_outcome(), expected)

    def test_matchup_swap_symmetry(self):
        home = Model(None, [], [])
        away = Model(None, [], [])
        home.predict_cat_outcome = Mock(return_value=Outcome(.6, .3, .1))
        away.predict_cat_outcome = Mock(return_value=Outcome(.3, .6, .1))
        result = home.predict_outcome()
        swapped = away.predict_outcome()
        self.assertOutcome(result, (swapped.away, swapped.home, swapped.tie))

    def test_no_ties_retains_previous_matchup_result(self):
        model = Model(None, [], [])
        model.predict_cat_outcome = Mock(return_value=Outcome(.4, .6, 0))
        self.assertAlmostEqual(model.predict_win(), .26656768)

    def test_invalid_category(self):
        with self.assertRaises(ValueError):
            Model(None, [], []).predict_cat_outcome('INVALID')


if __name__ == '__main__':
    unittest.main(verbosity=2)
