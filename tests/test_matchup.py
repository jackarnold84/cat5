import unittest
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np

from cat5.matchup import Lineup, Matchup, random_draw, start_is_available
from cat5.model import Outcome


class TestLineupDecisions(unittest.TestCase):
    def matchup(self, weights, cap=3, objective=None, away=False):
        players = [SimpleNamespace(
            playerId=i, percent_owned=100-i, injured=False, injuryStatus='ACTIVE',
            schedule={'1': {'date': datetime(2025, 1, 10)}},
        ) for i in range(1, len(weights)+1)]
        team = SimpleNamespace(team_id=1, roster=players)
        other = SimpleNamespace(team_id=2, roster=[])
        box = SimpleNamespace(home_team=team, away_team=other,
                              home_stats={'GP': {'value': 0}},
                              away_stats={'GP': {'value': 0}},
                              home_lineup=[], away_lineup=[])
        period = SimpleNamespace(max_gp=cap, game_day_ids={'1'})
        matchup = Matchup(box, period, datetime(2025, 1, 9))
        lineup = matchup.home_lineup
        if away:
            matchup.away_lineup = lineup
        objective = objective or (lambda starts: .5 + sum(weights[s.player.playerId-1]
                                                        for s in starts))

        def model():
            value = objective(lineup.lineup)
            return SimpleNamespace(predict_outcome=lambda: (
                Outcome(1-value-.1, value, .1) if away else Outcome(value, 1-value-.1, .1)))
        matchup.get_model = Mock(side_effect=model)
        return matchup, lineup

    def test_multiple_empty_slots_and_paired_impact(self):
        matchup, lineup = self.matchup([.1, -.05, -.1])
        values = matchup.optimize_home_lineup(n=0)
        by_id = {v.player.playerId: v for v in values}
        self.assertEqual([s.player.playerId for s in lineup.lineup], [1])
        self.assertEqual(lineup.optimization['unused'], 2)
        self.assertEqual(by_id[1].decision, 'Start')
        self.assertEqual(by_id[2].decision, 'Sit')
        self.assertAlmostEqual(by_id[1].value, .1)
        self.assertAlmostEqual(by_id[2].value, -.05)
        self.assertEqual(by_id[3].recommended, 0)
        self.assertEqual({r['starts'] for r in lineup.optimization['winByStarts']}, {0, 1, 2, 3})

    def test_no_starts_can_be_best(self):
        matchup, lineup = self.matchup([-.1, -.05])
        values = matchup.optimize_home_lineup(n=0)
        self.assertEqual(lineup.lineup, [])
        self.assertEqual(lineup.optimization['unused'], 3)
        self.assertTrue(all(v.decision == 'Sit' for v in values))

    def test_alternative_has_opportunity_cost_and_ownership_does_not_rank(self):
        matchup, lineup = self.matchup([.05, .1], cap=1)
        values = matchup.optimize_home_lineup(n=0)
        self.assertEqual(lineup.lineup[0].player.playerId, 2)
        self.assertEqual(values[0].player.playerId, 2)
        self.assertAlmostEqual(values[0].value, .05)
        self.assertAlmostEqual(values[1].value, -.05)

    def test_close_choices_are_consider_and_exact_ties_use_no_games(self):
        matchup, lineup = self.matchup([.001, 0])
        values = matchup.optimize_home_lineup(n=0)
        self.assertTrue(all(v.decision == 'Consider' for v in values))
        self.assertEqual(len(lineup.lineup), 1)

    def test_cap_zero_and_over_cap_never_selects_starts(self):
        for cap in [0, -2]:
            matchup, lineup = self.matchup([.1], cap=cap)
            values = matchup.optimize_home_lineup(n=0)
            self.assertEqual(lineup.lineup, [])
            self.assertEqual(values[0].decision, 'Cap reached')
            self.assertEqual(values[0].value, 0)

    def test_away_optimizer_uses_outright_away_win_probability(self):
        matchup, lineup = self.matchup([.05, .1], cap=1, away=True)
        values = matchup.optimize_away_lineup(n=0)
        self.assertEqual(values[0].player.playerId, 2)
        self.assertEqual(lineup.lineup[0].player.playerId, 2)

    def test_equivalent_dates_for_same_player_are_mixed_considerations(self):
        matchup, lineup = self.matchup([.1], cap=1)
        player = lineup.team.roster[0]
        player.schedule['2'] = {'date': datetime(2025, 1, 11)}
        matchup.matchup_period.game_day_ids.add('2')
        matchup.home_lineup = Lineup(lineup.team, matchup)
        # The synthetic model references the rebuilt lineup.
        lineup = matchup.home_lineup
        matchup.get_model = Mock(side_effect=lambda: SimpleNamespace(
            predict_outcome=lambda: Outcome(.5 + .1 * len(lineup.lineup),
                                            .4 - .1 * len(lineup.lineup), .1)))
        values = matchup.optimize_home_lineup(n=0)
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0].recommended, 1)
        self.assertEqual(values[0].eligible, 2)
        self.assertEqual(values[0].decision, 'Consider')
        self.assertAlmostEqual(values[0].value, 0)

    def test_random_lineups_cover_zero_to_full_and_never_repeat_games(self):
        _, lineup = self.matchup([.1, .1, .1])
        np.random.seed(21)
        counts = set()
        for _ in range(100):
            lineup.set_randomly()
            counts.add(len(lineup.lineup))
            self.assertEqual(len(set(lineup.lineup)), len(lineup.lineup))
        self.assertEqual(counts, {0, 1, 2, 3})
        self.assertEqual(random_draw([], 0, []), [])
        self.assertEqual(len(random_draw(['a', 'b'], 2, [0, 0])), 2)
        self.assertEqual(len(random_draw(['a', 'b', 'c'], 2, [0, 1, 0])), 2)

    def test_missing_roster_box_stats_and_unavailable_players_are_visible(self):
        matchup, lineup = self.matchup([.1])
        lineup.eligible_starts = []
        lineup.lineup = []
        values = matchup.optimize_home_lineup(n=0)
        self.assertEqual(values[0].scheduled, 1)
        self.assertEqual(values[0].eligible, 0)
        self.assertEqual(values[0].decision, 'Unavailable')

    def test_injury_return_eligibility(self):
        today = date(2025, 1, 9)
        player = SimpleNamespace(injured=True, injuryStatus='OUT')
        self.assertFalse(start_is_available(player, today + timedelta(days=3), today))
        player.estimated_return = today + timedelta(days=2)
        self.assertFalse(start_is_available(player, today + timedelta(days=1), today))
        self.assertTrue(start_is_available(player, today + timedelta(days=2), today))
        player.estimated_return = today
        self.assertFalse(start_is_available(player, today + timedelta(days=2), today))
        player.injuryStatus = 'SUSPENSION'
        player.estimated_return = today + timedelta(days=1)
        self.assertFalse(start_is_available(player, today + timedelta(days=2), today))
        player.injured = False
        player.injuryStatus = 'ACTIVE'
        self.assertTrue(start_is_available(player, today, today))
