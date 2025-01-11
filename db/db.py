import base64
import gzip
import json
import os
from typing import Any, Dict

import boto3

DYNAMO_TABLE_NAME = "MyTable"


class Database:
    dynamo = boto3.resource("dynamodb")

    def __init__(self, table_name=DYNAMO_TABLE_NAME):
        self.table = self.dynamo.Table(table_name)
        self.read_mock = os.environ.get('DB_READ', '').lower() != 'prod'
        self.write_mock = os.environ.get('DB_WRITE', '').lower() != 'prod'

        self.mock_db_dir = os.path.join('.mock-db', table_name)
        if self.write_mock:
            os.makedirs(self.mock_db_dir, exist_ok=True)

        print(
            f'--> db initialized: '
            f'READ={"PROD" if not self.read_mock else "MOCK"} '
            f'WRITE={"PROD" if not self.write_mock else "MOCK"}'
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

    def write(self, key: str, data: dict) -> None:
        if self.write_mock:
            self._mock_write(key, data)
        else:
            self._prod_write(key, data)

    def _mock_write(self, key: str, data: dict) -> None:
        loc = os.path.join(self.mock_db_dir, f'{key}.json')
        with open(loc, 'w') as f:
            json.dump(data, f, indent=4)
        print(f'--> mock db write: {loc}')

    def _prod_write(self, key: str, data: dict) -> None:
        json_data = json.dumps(data)
        compressed_data = gzip.compress(json_data.encode('utf-8'))
        base64_data = base64.b64encode(compressed_data).decode('utf-8')
        self.table.put_item(Item={'key': key, 'data': base64_data})
        print(f'--> prod db write: {key}')
