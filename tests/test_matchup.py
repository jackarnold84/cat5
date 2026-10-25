import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from cat5.matchup import Matchup, random_draw


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
        starter = SimpleNamespace(player=SimpleNamespace(playerId=1, percent_owned=80))
        other = SimpleNamespace(player=SimpleNamespace(playerId=2, percent_owned=20))
        lineup = SimpleNamespace(lineup=[starter])
        lineup.set_randomly = Mock(side_effect=lambda **_: setattr(lineup, 'lineup', [other]))
        matchup = object.__new__(Matchup)
        matchup.home_lineup = lineup
        matchup.get_model = Mock(side_effect=[
            SimpleNamespace(predict_win=lambda: 0.8),
            SimpleNamespace(predict_win=lambda: 0.2),
        ])

        values = matchup.optimize_home_lineup(n=1)

        self.assertEqual(lineup.lineup, [starter])
        self.assertEqual({value.player.playerId for value in values}, {1, 2})


if __name__ == '__main__':
    unittest.main(verbosity=2)
