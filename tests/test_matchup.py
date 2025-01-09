import unittest

from cat5.matchup import random_draw


class TestModel(unittest.TestCase):
    def setUp(self):
        print('--> running')

    def test_random_draw(self):
        arr = ['a', 'b', 'c', 'd']
        n = 2
        w_arr = [0.0, 0.7, 0.6, 0.9]
        result = random_draw(arr, n, w_arr)
        self.assertEqual(len(result), n)


if __name__ == '__main__':
    unittest.main(verbosity=2)
