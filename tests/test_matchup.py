import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from cat5.matchup import Matchup, random_draw
from cat5.model import Outcome


class TestModel(unittest.TestCase):
    def setUp(self):
        print('--> running')

    def test_random_draw(self):
        arr = ['a', 'b', 'c', 'd']
        n = 2
        w_arr = [0.0, 0.7, 0.6, 0.9]
        result = random_draw(arr, n, w_arr)
        self.assertEqual(len(result), n)

    def test_optimizer_keeps_undrawn_starting_player(self):
        starter = SimpleNamespace(
            player=SimpleNamespace(playerId=1, percent_owned=80))
        other = SimpleNamespace(
            player=SimpleNamespace(playerId=2, percent_owned=20))
        lineup = SimpleNamespace(lineup=[starter])
        lineup.set_randomly = Mock(
            side_effect=lambda **_: setattr(lineup, 'lineup', [other]))
        matchup = object.__new__(Matchup)
        matchup.home_lineup = lineup
        matchup.get_model = Mock(side_effect=[
            SimpleNamespace(predict_outcome=lambda: Outcome(0.8, 0.2, 0)),
            SimpleNamespace(predict_outcome=lambda: Outcome(0.2, 0.8, 0)),
        ])

        values = matchup.optimize_home_lineup(n=1)

        self.assertEqual(lineup.lineup, [starter])
        self.assertEqual({value.player.playerId for value in values}, {1, 2})

    def test_away_optimizer_maximizes_outright_wins(self):
        starter = SimpleNamespace(
            player=SimpleNamespace(playerId=1, percent_owned=80))
        other = SimpleNamespace(
            player=SimpleNamespace(playerId=2, percent_owned=20))
        lineup = SimpleNamespace(lineup=[starter])
        lineup.set_randomly = Mock(
            side_effect=lambda **_: setattr(lineup, 'lineup', [other]))
        matchup = object.__new__(Matchup)
        matchup.away_lineup = lineup
        matchup.get_model = Mock(side_effect=[
            SimpleNamespace(predict_outcome=lambda: Outcome(.4, .5, .1)),
            SimpleNamespace(predict_outcome=lambda: Outcome(.3, .2, .5)),
        ])
        values = matchup.optimize_away_lineup(n=1)
        self.assertEqual(lineup.lineup, [starter])
        self.assertAlmostEqual(values[0].value, 1)
        self.assertAlmostEqual(values[1].value, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
