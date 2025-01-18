import base64
import gzip
import json
import os
from typing import Any, Dict

import boto3

TABLE_NAME = os.environ.get("TABLE_NAME", "Cat5Table")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-2")


class DBReader:
    dynamo = boto3.resource("dynamodb", region_name=AWS_REGION)

    def __init__(self, table_name=TABLE_NAME):
        self.table = self.dynamo.Table(table_name)
        self.read_mock = os.environ.get('DB_READ', '').lower() != 'prod'

        self.mock_db_dir = os.path.join('.mock-db', table_name)
        print(
            f'--> db initialized: '
            f'READ={"PROD" if not self.read_mock else "MOCK"}'
        )

    def read(self, key: str) -> Dict[str, Any]:
        if self.read_mock:
            return self._mock_read(key)
        else:
            return self._prod_read(key)

    def _mock_read(self, key: str) -> Dict[str, Any]:
        loc = os.path.join(self.mock_db_dir, f'{key}.json')
        with open(loc, 'r') as f:
            data = json.load(f)
        print(f'--> mock db read: {loc}')
        return data

    def _prod_read(self, key: str) -> Dict[str, Any]:
        resp = self.table.get_item(Key={'key': key})
        if 'Item' not in resp:
            raise KeyError(f'key not found in DB: {key}')
        if 'data' not in resp['Item']:
            raise KeyError(f'data field not found in DB for key: {key}')
        base64_data = resp['Item']['data']
        compressed_data = base64.b64decode(base64_data)
        json_data = gzip.decompress(compressed_data).decode('utf-8')
        data_dict = json.loads(json_data)
        print(f'--> prod db read: {key}')
        return data_dict
