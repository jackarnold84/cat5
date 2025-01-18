import json
import os
import sys
import time
from dataclasses import asdict
from datetime import datetime

import boto3
from aws_lambda_powertools.utilities.typing import LambdaContext

from api.handler import lambda_handler as api_handler
from processor.handler import LambdaPayload
from processor.handler import lambda_handler as processor_handler


class Cat5Stack:
    def processor_lambda(self, event: dict) -> dict:
        return processor_handler(event, LambdaContext())

    def api_lambda(self, event: dict) -> dict:
        return api_handler(event, LambdaContext())


class Cat5CloudStack(Cat5Stack):
    def __init__(self):
        self.processor_lambda_name = 'Cat5Processor'
        self.api_lambda_name = 'Cat5Api'
        self.lambda_client = boto3.client(
            'lambda',
            region_name=os.environ.get('AWS_REGION', 'us-east-2'),
        )

    def processor_lambda(self, event: dict) -> dict:
        response = self.lambda_client.invoke(
            FunctionName=self.processor_lambda_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(event)
        )
        response_payload = json.load(response['Payload'])
        return response_payload

    def api_lambda(self, event: dict) -> dict:
        time.sleep(3)
        response = self.lambda_client.invoke(
            FunctionName=self.api_lambda_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(event)
        )
        response_payload = json.load(response['Payload'])
        return response_payload


def integration_test(stack: Cat5Stack):
    os.environ['DB_READ'] = 'MOCK'
    os.environ['DB_WRITE'] = 'MOCK'
    test_start_timestamp = int(datetime.now().timestamp())

    # processor
    print('--> [testing processor handler]')
    processor_event = LambdaPayload(
        tag='test',
        leagueId='501268457',
        year=2025,
    )
    processor_resp = stack.processor_lambda(asdict(processor_event))
    print(f'processor_resp: {processor_resp}')
    assert processor_resp['status'] == 'SUCCESS'

    # api
    print('--> [testing api handler]')
    api_event = {
        'path': '/cat5/data/test',
        'httpMethod': 'GET',
        'pathParameters': {
            'tag': 'test',
        },
        'queryStringParameters': {
            'cache': 'none',
        },
    }
    api_resp = stack.api_lambda(api_event)
    if api_resp['statusCode'] != 200:
        print(f'api_resp: {api_resp}')
        raise Exception('api handler failed')
    print(f'statusCode: {api_resp["statusCode"]}')
    body_dict = json.loads(api_resp['body'])
    assert body_dict['updateTimestamp'] >= test_start_timestamp


if __name__ == '__main__':
    stack: Cat5Stack = Cat5Stack()
    if len(sys.argv) > 1 and sys.argv[1] in ['cloud', '--cloud']:
        print('--> [running cloud integration test]')
        stack = Cat5CloudStack()
    else:
        print('--> [running local integration test]')

    integration_test(stack)
