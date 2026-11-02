import unittest
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import requests  # type: ignore[import-untyped]

from processor.injuries import load_return_estimates


class TestInjuryEstimates(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
        self.player = SimpleNamespace(playerId=123)
        self.league = SimpleNamespace(year=2027, teams=[SimpleNamespace(roster=[self.player])])
        self.data = {
            'timestamp': '2026-11-01T11:00Z', 'season': {'year': 2027},
            'injuries': [{'injuries': [{
                'athlete': {'id': '123'}, 'details': {'returnDate': '2026-11-03'},
                'shortComment': 'Recheck Tuesday.',
            }]}],
        }

    @patch('processor.injuries.requests.get')
    def test_return_date_and_note_preserved(self, get):
        get.return_value.json.return_value = self.data
        load_return_estimates(self.league, self.now)
        self.assertEqual(self.player.estimated_return, date(2026, 11, 3))
        self.assertEqual(self.player.injury_note, 'Recheck Tuesday.')
        self.assertEqual(get.call_args.kwargs['timeout'], 8)

    @patch('processor.injuries.requests.get')
    def test_id_from_athlete_link(self, get):
        athlete = self.data['injuries'][0]['injuries'][0]['athlete']
        athlete.clear()
        athlete['links'] = [{'href': 'https://www.espn.com/nba/player/_/id/123/test'}]
        get.return_value.json.return_value = self.data
        load_return_estimates(self.league, self.now)
        self.assertEqual(self.player.estimated_return, date(2026, 11, 3))

    @patch('processor.injuries.requests.get')
    def test_historical_season_does_not_fetch_live_injuries(self, get):
        self.league.year = 2025
        load_return_estimates(self.league, self.now)
        get.assert_not_called()

    @patch('processor.injuries.requests.get')
    def test_stale_feed_or_wrong_season_ignored(self, get):
        for field, value in [('timestamp', '2026-10-29T11:00Z'), ('season', {'year': 2026})]:
            with self.subTest(field=field):
                data = dict(self.data, **{field: value})
                get.return_value.json.return_value = data
                load_return_estimates(self.league, self.now)
                self.assertFalse(hasattr(self.player, 'estimated_return'))

    @patch('processor.injuries.requests.get')
    def test_missing_invalid_or_past_return_is_not_invented(self, get):
        for value in [None, 'bad-date', '2026-10-30', '2026-11-01']:
            with self.subTest(value=value):
                self.data['injuries'][0]['injuries'][0]['details']['returnDate'] = value
                get.return_value.json.return_value = self.data
                load_return_estimates(self.league, self.now)
                self.assertFalse(hasattr(self.player, 'estimated_return'))

    @patch('processor.injuries.requests.get', side_effect=requests.Timeout)
    def test_feed_failure_is_optional(self, _get):
        load_return_estimates(self.league, self.now)
        self.assertFalse(hasattr(self.player, 'estimated_return'))
