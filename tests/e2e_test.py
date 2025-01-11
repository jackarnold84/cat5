import os
from dataclasses import asdict

from processor.handler import LambdaPayload, handler


def test_e2e():
    """
    Runs the handler function with live espn data and mocked db
    """
    os.environ['DB_READ'] = 'MOCK'
    os.environ['DB_WRITE'] = 'MOCK'

    input_payload = LambdaPayload(
        tag='test',
        leagueId='501268457',
        year=2025,
    )
    lambda_response = handler(asdict(input_payload), None)

    print(lambda_response)
    assert lambda_response['status'] == 'SUCCESS'


if __name__ == '__main__':
    test_e2e()
