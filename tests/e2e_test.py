import json
import os
from dataclasses import asdict
from datetime import datetime

from api.handler import APIGatewayEvent
from api.handler import handler as api_handler
from processor.handler import LambdaPayload
from processor.handler import handler as processor_handler


def test_e2e():
    """
    Runs the handler function with live espn data and mocked db
    """
    os.environ['DB_READ'] = 'MOCK'
    os.environ['DB_WRITE'] = 'MOCK'
    test_start_timestamp = int(datetime.now().timestamp())

    # processor
    print('--- testing processor handler ---')
    processor_event = LambdaPayload(
        tag='test',
        leagueId='501268457',
        year=2025,
    )
    processor_resp = processor_handler(asdict(processor_event), None)
    print(processor_resp)
    assert processor_resp['status'] == 'SUCCESS'

    # api
    print('--- testing api handler ---')
    api_event = APIGatewayEvent(
        path='/data',
        httpMethod='GET',
        queryStringParameters={'tag': 'test'},
    )
    api_resp = api_handler(asdict(api_event), None)
    assert api_resp['statusCode'] == 200
    print(f'statusCode: {api_resp["statusCode"]}')
    body_dict = json.loads(api_resp['body'])
    assert body_dict['updateTimestamp'] >= test_start_timestamp


if __name__ == '__main__':
    test_e2e()
