import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import call, patch

from scripts.set_espn_auth import main


class TestSetEspnAuth(unittest.TestCase):
    @patch('scripts.set_espn_auth.getpass.getpass')
    @patch('scripts.set_espn_auth.boto3.Session')
    def test_saves_secure_parameter_in_expected_account(self, session_class, prompt):
        session = session_class.return_value
        session.client.return_value.get_caller_identity.return_value = {
            'Account': '209417694225',
        }
        prompt.side_effect = ['example-s2', '{example-swid}']

        output = io.StringIO()
        with redirect_stdout(output):
            main()

        session_class.assert_called_once_with(region_name='us-east-2')
        self.assertEqual(session.client.call_args_list, [call('sts'), call('ssm')])
        args = session.client.return_value.put_parameter.call_args.kwargs
        self.assertEqual(args['Name'], '/cat5/espn-auth')
        self.assertEqual(args['Type'], 'SecureString')
        self.assertTrue(args['Overwrite'])
        self.assertEqual(
            json.loads(args['Value']),
            {'espn_s2': 'example-s2', 'SWID': '{example-swid}'},
        )
        self.assertNotIn('example-s2', output.getvalue())

    @patch('scripts.set_espn_auth.getpass.getpass')
    @patch('scripts.set_espn_auth.boto3.Session')
    def test_wrong_account_stops_before_prompt(self, session_class, prompt):
        session_class.return_value.client.return_value.get_caller_identity.return_value = {
            'Account': '000000000000',
        }

        with self.assertRaisesRegex(SystemExit, 'Wrong AWS account'):
            main()

        prompt.assert_not_called()
