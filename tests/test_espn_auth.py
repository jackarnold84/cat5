import os
import unittest
from unittest.mock import patch

from espn_api.requests.espn_requests import ESPNAccessDenied

from processor.espn_auth import league_credentials
from processor.handler import handler


class TestEspnAuth(unittest.TestCase):
    @patch.dict(os.environ, {'ESPN_AUTH_PARAMETER': '/cat5/espn-auth'})
    @patch('processor.espn_auth.boto3.client')
    def test_secure_parameter_passes_cookies_to_league(self, client):
        client.return_value.get_parameter.return_value = {
            'Parameter': {
                'Type': 'SecureString',
                'Value': '{"espn_s2":"test-s2","SWID":"{test-swid}"}',
            },
        }

        self.assertEqual(
            league_credentials(),
            {'espn_s2': 'test-s2', 'swid': '{test-swid}'},
        )
        client.return_value.get_parameter.assert_called_once_with(
            Name='/cat5/espn-auth', WithDecryption=True,
        )

    @patch.dict(os.environ, {'ESPN_AUTH_PARAMETER': '/cat5/espn-auth'})
    @patch('processor.espn_auth.boto3.client')
    def test_plaintext_parameter_is_rejected(self, client):
        client.return_value.get_parameter.return_value = {
            'Parameter': {'Type': 'String', 'Value': '{}'},
        }
        with self.assertRaisesRegex(ValueError, 'SecureString'):
            league_credentials()

    @patch('processor.handler.DBWriter')
    @patch('processor.handler.league_credentials')
    @patch('processor.handler.League')
    def test_espn_error_does_not_expose_cookies(self, league, credentials, _db):
        credentials.return_value = {'espn_s2': 'secret-s2', 'swid': 'secret-swid'}
        league.side_effect = ESPNAccessDenied('espn_s2=secret-s2')

        with self.assertRaises(RuntimeError) as raised:
            handler({'tag': 'demon', 'leagueId': '501268457', 'year': 2027}, None)

        self.assertNotIn('secret-s2', str(raised.exception))
        self.assertIsNone(raised.exception.__cause__)
