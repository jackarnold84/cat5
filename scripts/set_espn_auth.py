"""Store private ESPN league cookies in AWS Parameter Store."""

import getpass
import json

import boto3


AWS_ACCOUNT = '209417694225'
AWS_REGION = 'us-east-2'
PARAMETER_NAME = '/cat5/espn-auth'


def main() -> None:
    session = boto3.Session(region_name=AWS_REGION)
    account = session.client('sts').get_caller_identity()['Account']
    if account != AWS_ACCOUNT:
        raise SystemExit(f'Wrong AWS account: {account}')

    espn_s2 = getpass.getpass('espn_s2: ')
    swid = getpass.getpass('SWID (include the braces): ')
    if not espn_s2.strip() or not (swid.startswith('{') and swid.endswith('}')):
        raise SystemExit('Missing espn_s2 or invalid SWID')

    session.client('ssm').put_parameter(
        Name=PARAMETER_NAME,
        Value=json.dumps({'espn_s2': espn_s2, 'SWID': swid}),
        Type='SecureString',
        Overwrite=True,
    )
    print(f'Saved {PARAMETER_NAME}')


if __name__ == '__main__':
    main()
