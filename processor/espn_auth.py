import json
import os
from typing import Dict

import boto3


def league_credentials() -> Dict[str, str]:
    parameter_name = os.environ.get('ESPN_AUTH_PARAMETER')
    if not parameter_name:
        return {}

    response = boto3.client('ssm').get_parameter(
        Name=parameter_name,
        WithDecryption=True,
    )
    parameter = response['Parameter']
    if parameter['Type'] != 'SecureString':
        raise ValueError('ESPN auth parameter must be a SecureString')

    try:
        cookies = json.loads(parameter['Value'])
        espn_s2 = cookies['espn_s2']
        swid = cookies['SWID']
    except (KeyError, TypeError, ValueError):
        raise ValueError('ESPN auth parameter must contain espn_s2 and SWID') from None

    if not isinstance(espn_s2, str) or not espn_s2:
        raise ValueError('ESPN auth parameter has an invalid espn_s2')
    if not isinstance(swid, str) or not swid:
        raise ValueError('ESPN auth parameter has an invalid SWID')

    return {'espn_s2': espn_s2, 'swid': swid}
