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
    alpha = 2 / 31
    value = prior if prior is not None else observations[0]
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
        expected = smooth([5] * 30 + [20] * 5 + [100 / 3] * 3 + [50] * 2, 999)
        self.assertAlmostEqual(start.projection('PTS'), expected)

    def test_short_season_retains_existing_preseason_blend(self):
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

    def test_preseason_influence_fades_smoothly_through_game_30(self):
        forecasts = []
        for gp in (29, 30, 31, 82):
            start = make_start({'total': split(gp, PTS=10 * gp)}, {'PTS': 30})
            value = start.projection('PTS')
            self.assertAlmostEqual(value, 10 + 20 * (29 / 31) ** gp)
            self.assertGreater(value, 10)
            forecasts.append(value)
        self.assertGreater(forecasts[0], forecasts[1])
        self.assertGreater(forecasts[1], forecasts[2])
        self.assertLess(forecasts[0] - forecasts[1], .2)

    def test_same_recent_change_has_same_effect_late_in_season(self):
        forecasts = []
        for gp in (30, 60, 82):
            start = make_start({'total': split(gp, PTS=(gp - 10) * 10 + 200),
                                'last_15': split(10, PTS=200)}, {'PTS': 10})
            forecasts.append(start.projection('PTS'))
        for value in forecasts:
            self.assertAlmostEqual(value, smooth([20] * 10, 10))

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
                expected = .1 * (99 / 101) + (1 - 99 / 101)
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

    def test_shooting_prior_and_history_use_attempt_weights(self):
        start = make_start({'total': split(2, FTA=12, FTM=6),
                            'last_7': split(1, FTA=2, FTM=2)},
                           {'FTA': 4, 'FTM': 3})
        expected_attempts = smooth([10, 2], 4)
        after_older = .75 * (119 / 121) ** 10 + .4 * (1 - (119 / 121) ** 10)
        expected_rate = after_older * (119 / 121) ** 2 + (1 - (119 / 121) ** 2)
        self.assertAlmostEqual(start.projection('FTM'), expected_attempts * expected_rate)
        self.assertAlmostEqual(start.projection('FTA'), expected_attempts)
        self.assertAlmostEqual(start.projection('FT%'), expected_rate)

    def test_shooting_evidence_depends_on_attempts_not_games(self):
        for cat, att, made in (('FG%', 'FGA', 'FGM'), ('FT%', 'FTA', 'FTM')):
            for gp in (1, 29, 30, 82):
                with self.subTest(cat=cat, gp=gp):
                    start = make_start({'total': split(gp, **{att: 1, made: 1})},
                                       {att: 4, made: 3})
                    self.assertAlmostEqual(start.projection(cat), .75 * 119 / 121 + 2 / 121)

    def test_more_attempts_shift_shooting_further_from_preseason(self):
        values = []
        for attempts in (1, 10, 100, 1000):
            start = make_start({'total': split(30, FTA=attempts, FTM=attempts)},
                               {'FTA': 4, 'FTM': 3})
            values.append(start.projection('FT%'))
        self.assertEqual(values, sorted(values))
        self.assertLess(values[0], .76)
        self.assertGreater(values[-1], .999)

    def test_no_attempts_preserve_accuracy_while_lowering_volume(self):
        start = make_start({'total': split(82, FTA=0, FTM=0)}, {'FTA': 4, 'FTM': 3})
        self.assertAlmostEqual(start.projection('FT%'), .75)
        self.assertGreater(start.projection('FTA'), 0)
        self.assertLess(start.projection('FTA'), .02)

    def test_no_attempt_recent_games_do_not_change_shooting_accuracy(self):
        start = make_start({'total': split(10, FTA=10, FTM=10),
                            'last_7': split(2, FTA=0, FTM=0)}, {'FTA': 4, 'FTM': 3})
        self.assertAlmostEqual(start.projection('FT%'), 1 - .25 * (119 / 121) ** 10)

    def test_low_volume_shooters_have_minimum_attempt_span(self):
        start = make_start({'total': split(30, FTA=1, FTM=1)}, {'FTA': 1, 'FTM': .75})
        self.assertAlmostEqual(start.projection('FT%'), .75 * 99 / 101 + 2 / 101)

    def test_high_volume_shooters_keep_original_game_scale(self):
        start = make_start({'total': split(1, FGA=20, FGM=20)}, {'FGA': 20, 'FGM': 10})
        # Twenty attempts are one typical game; preserve roughly a 30-game span.
        expected = 1 - .5 * (599 / 601) ** 20
        self.assertAlmostEqual(start.projection('FG%'), expected)
        self.assertAlmostEqual(expected, 1 - .5 * 29 / 31, delta=.0001)

    def test_shooting_updates_remain_bounded_for_extreme_data(self):
        for attempts, makes in ((1e-10, 0), (1e-10, 1e-10),
                                (1e308, 0), (1e308, 1e308)):
            with self.subTest(attempts=attempts, makes=makes):
                start = make_start({'total': split(82, FTA=attempts, FTM=makes)},
                                   {'FTA': 4, 'FTM': 3})
                rate = start.projection('FT%')
                self.assertTrue(math.isfinite(rate))
                self.assertGreaterEqual(rate, 0)
                self.assertLessEqual(rate, 1)
                self.assertLessEqual(start.projection('FTM'), start.projection('FTA'))

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
