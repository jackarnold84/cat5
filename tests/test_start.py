import math
import pickle
import unittest
from datetime import datetime
from types import SimpleNamespace

from cat5.model import count_cats
from cat5.start import EmptyStart, PlayerStart, ema_next


def make_start(periods=None, prior=None):
    stats = {f'2027_{period}': split for period, split in (periods or {}).items()}
    if prior is not None:
        stats['2027_projected'] = {'avg': prior}
    player = SimpleNamespace(stats=stats, year=2027, injured=False,
                             schedule={'1': {'date': datetime(2026, 11, 1)}})
    return PlayerStart(player, '1')


def split(gp, **counts):
    return {'total': {'GP': gp, **counts}}


def smooth(observations, prior=None):
    """Independent, per-observation reference for the grouped calculation."""
    span = max(30, len(observations))
    alpha = 2 / (span + 1)
    value = prior if prior is not None and len(observations) < 30 else observations[0]
    for observation in observations:
        value = alpha * observation + (1 - alpha) * value
    return value


class TestPlayerProjection(unittest.TestCase):
    def test_each_game_contributes_once_in_chronological_order(self):
        start = make_start({
            'total': split(40, PTS=450),
            'last_30': split(10, PTS=300),
            'last_15': split(5, PTS=200),
            'last_7': split(2, PTS=100),
        }, {'PTS': 999})
        expected = smooth([5] * 30 + [20] * 5 + [100 / 3] * 3 + [50] * 2)
        self.assertAlmostEqual(start.projection('PTS'), expected)

    def test_short_season_uses_prior_only_for_unobserved_history(self):
        start = make_start({'total': split(2, PTS=30),
                            'last_7': split(1, PTS=20)}, {'PTS': 5})
        self.assertAlmostEqual(start.projection('PTS'), ema_next([5] * 28 + [10, 20]))

    def test_equal_game_windows_do_not_duplicate_observations(self):
        start = make_start({p: split(2, PTS=30)
                            for p in ('total', 'last_30', 'last_15', 'last_7')},
                           {'PTS': 5})
        self.assertAlmostEqual(start.projection('PTS'), smooth([15, 15], 5))

    def test_constant_production(self):
        for gp in (1, 29, 30, 82):
            with self.subTest(gp=gp):
                start = make_start({'total': split(gp, PTS=12 * gp)}, {'PTS': 12})
                self.assertAlmostEqual(start.projection('PTS'), 12)

    def test_missing_prior_does_not_add_zero_games(self):
        start = make_start({'total': split(2, PTS=30), 'last_7': split(1, PTS=20)})
        self.assertAlmostEqual(start.projection('PTS'), smooth([10, 20]))

    def test_zero_prior_is_not_missing(self):
        start = make_start({'total': split(1, PTS=10)}, {'PTS': 0})
        self.assertAlmostEqual(start.projection('PTS'), 20 / 31)

    def test_missing_observations_fall_back_to_prior(self):
        for periods in ({}, {'total': split(0, PTS=0)}, {'total': None},
                        {'total': {'total': None, 'avg': None}}):
            with self.subTest(periods=periods):
                self.assertEqual(make_start(periods, {'PTS': 12}).projection('PTS'), 12)
                self.assertEqual(make_start(periods).projection('PTS'), 0)

    def test_null_averages_and_average_fallback(self):
        start = make_start({'total': {**split(2, PTS=24), 'avg': None}})
        start.player.stats['2027_projected'] = {'avg': None}
        self.assertEqual(start.projection('PTS'), 12)
        start = make_start({'total': {'total': {'GP': 2}, 'avg': {'PTS': 12}}})
        self.assertEqual(start.projection('PTS'), 12)

    def test_totals_take_precedence_over_averages(self):
        start = make_start({'total': {**split(2, PTS=24), 'avg': {'PTS': 999}}})
        self.assertEqual(start.projection('PTS'), 12)

    def test_overflowing_average_fallback_is_unavailable(self):
        start = make_start({'total': {'total': {'GP': 2}, 'avg': {'PTS': 1e308}}},
                           {'PTS': 8})
        self.assertEqual(start.projection('PTS'), 8)

    def test_invalid_numeric_inputs_are_not_observations(self):
        for value in (None, -1, float('nan'), float('inf'), '12', True, 10 ** 400):
            with self.subTest(value=value):
                start = make_start({'total': split(2, PTS=value)}, {'PTS': 8})
                self.assertEqual(start.projection('PTS'), 8)
                self.assertEqual(make_start(prior={'PTS': value}).projection('PTS'), 0)
        for gp in (None, -1, .5, float('nan'), float('inf'), True, '2'):
            with self.subTest(gp=gp):
                self.assertEqual(make_start({'total': split(gp, PTS=24)},
                                            {'PTS': 8}).projection('PTS'), 8)

    def test_contradictory_narrower_windows_are_skipped(self):
        for bad in (split(11, PTS=90), split(3, PTS=101), split(10, PTS=90)):
            with self.subTest(bad=bad):
                start = make_start({'total': split(10, PTS=100), 'last_30': bad,
                                    'last_7': split(2, PTS=40)})
                self.assertAlmostEqual(start.projection('PTS'), smooth([7.5] * 8 + [20] * 2))

    def test_missing_category_does_not_mean_zero(self):
        start = make_start({'total': split(10, PTS=100), 'last_7': split(2)})
        self.assertEqual(start.projection('PTS'), 10)

    def test_narrower_window_can_be_used_without_season_data(self):
        start = make_start({'last_15': split(4, PTS=40), 'last_7': split(2, PTS=30)})
        self.assertAlmostEqual(start.projection('PTS'), smooth([5, 5, 15, 15]))

    def test_shooting_uses_attempt_volume_and_matches_count_projections(self):
        for cat, att, made in (('FG%', 'FGA', 'FGM'), ('FT%', 'FTA', 'FTM')):
            with self.subTest(cat=cat):
                start = make_start({'total': split(2, **{att: 11, made: 2}),
                                    'last_7': split(1, **{att: 1, made: 1})})
                expected = smooth([1, 1]) / smooth([10, 1])
                self.assertAlmostEqual(start.projection(cat), expected)
                self.assertAlmostEqual(start.projection(cat) * start.projection(att),
                                       start.projection(made))

    def test_shooting_zero_attempts_and_boundary_rates(self):
        for att, made, expected in ((0, 0, 0), (10, 0, 0), (10, 10, 1)):
            with self.subTest(att=att, made=made):
                start = make_start({'total': split(2, FTA=att, FTM=made)})
                self.assertEqual(start.projection('FT%'), expected)

    def test_shooting_missing_or_impossible_pairs_use_broader_data(self):
        for bad in (split(1, FTA=1), split(1, FTA=1, FTM=2),
                    split(1, FTA=9, FTM=0)):
            with self.subTest(bad=bad):
                # Last case would imply one older attempt with five makes.
                start = make_start({'total': split(2, FTA=10, FTM=5), 'last_7': bad})
                self.assertEqual(start.projection('FT%'), .5)
                self.assertEqual(start.projection('FTA'), 5)
                self.assertEqual(start.projection('FTM'), 2.5)

    def test_shooting_prior_uses_counts_instead_of_rounded_percentage(self):
        start = make_start(prior={'FTA': 3, 'FTM': 2, 'FT%': .667})
        self.assertEqual(start.projection('FT%'), 2 / 3)
        for prior in ({'FTA': 2}, {'FTA': 2, 'FTM': 3}, {'FT%': .8}):
            with self.subTest(prior=prior):
                self.assertEqual(make_start(prior=prior).projection('FT%'), 0)

    def test_shooting_prior_and_history_share_weights(self):
        start = make_start({'total': split(2, FTA=12, FTM=6),
                            'last_7': split(1, FTA=2, FTM=2)},
                           {'FTA': 4, 'FTM': 3})
        expected_makes = smooth([4, 2], 3)
        expected_attempts = smooth([10, 2], 4)
        self.assertAlmostEqual(start.projection('FTM'), expected_makes)
        self.assertAlmostEqual(start.projection('FTA'), expected_attempts)
        self.assertAlmostEqual(start.projection('FT%'), expected_makes / expected_attempts)

    def test_tiny_valid_counts_are_preserved(self):
        start = make_start({'total': split(1, FTA=1e-10, FTM=5e-11)})
        self.assertEqual(start.projection('FT%'), .5)

    def test_roundoff_does_not_discard_consistent_windows(self):
        start = make_start({'total': split(3, PTS=.3), 'last_7': split(2, PTS=.1 + .2)})
        self.assertAlmostEqual(start.projection('PTS'), smooth([0, .15, .15]))

    def test_empty_start_and_empty_ema(self):
        for cat in (*count_cats, 'FG%', 'FT%', 'FGA', 'FGM', 'FTA', 'FTM'):
            self.assertEqual(EmptyStart().projection(cat), 0)
        self.assertEqual(ema_next([]), 0)

    def test_saved_rosters_have_finite_coherent_projections(self):
        with open('tests/pickles/league_20250109.pkl', 'rb') as file:
            league = pickle.load(file)
        for team in league.teams:
            for player in team.roster:
                start = PlayerStart(player, next(iter(player.schedule)))
                for cat in (*count_cats, 'FG%', 'FT%', 'FGA', 'FGM', 'FTA', 'FTM'):
                    with self.subTest(player=player.name, cat=cat):
                        value = start.projection(cat)
                        self.assertTrue(math.isfinite(value))
                        self.assertGreaterEqual(value, 0)
                for cat, att, made in (('FG%', 'FGA', 'FGM'), ('FT%', 'FTA', 'FTM')):
                    self.assertLessEqual(start.projection(cat), 1)
                    self.assertAlmostEqual(start.projection(cat) * start.projection(att),
                                           start.projection(made))


if __name__ == '__main__':
    unittest.main()
