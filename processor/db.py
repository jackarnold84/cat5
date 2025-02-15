import base64
import gzip
import json
import os

import boto3

TABLE_NAME = os.environ.get("TABLE_NAME", "Cat5Table")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-2")


class DBWriter:
    dynamo = boto3.resource("dynamodb", region_name=AWS_REGION)

    def __init__(self, table_name=TABLE_NAME):
        self.table = self.dynamo.Table(table_name)
        self.write_mock = os.environ.get('DB_WRITE', '').lower() != 'prod'

        self.mock_db_dir = os.path.join('.mock-db', table_name)
        if self.write_mock:
            os.makedirs(self.mock_db_dir, exist_ok=True)

        print(
            f'--> db initialized: '
            f'WRITE={"PROD" if not self.write_mock else "MOCK"}'
        )

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
