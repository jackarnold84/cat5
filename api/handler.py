import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, NamedTuple, Optional

from .db import DBReader


class CacheItem(NamedTuple):
    data: Dict[str, Any]
    ttl: float


@dataclass
class APIGatewayEvent:
    path: str
    httpMethod: str
    queryStringParameters: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None


TTL = 300  # 5 minutes
cache: Dict[str, CacheItem] = {}
db = DBReader()


def lambda_handler(event: Dict[str, Any], _) -> Dict[str, Any]:
    try:
        return handler(event, _)
    except Exception as e:
        return api_response(500, {'error': f'unexpected error: {e}'})


def handler(event: Dict[str, Any], _) -> Dict[str, Any]:
    try:
        api_event = APIGatewayEvent(**event)
        tag = api_event.queryStringParameters['tag']
        cache_param = api_event.queryStringParameters.get('cache', '')
    except Exception as e:
        return api_response(400, {'error': f'bad request: {e}'})

    if api_event.path != '/data':
        return api_response(404, {'error': 'invalid path'})
    if api_event.httpMethod != 'GET':
        return api_response(405, {'error': 'method not allowed'})

    if tag in cache and cache_param != 'none':
        item = cache[tag]
        if item.ttl > time.time():
            return api_response(200, item.data)
        else:
            del cache[tag]

    try:
        data = db.read(tag)
    except KeyError:
        return api_response(404, {'error': f'not found: {tag}'})

    cache[tag] = CacheItem(data, time.time() + TTL)
    return api_response(200, data)


def api_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'application/json',
            'Access-Control-Allow-Methods': 'GET',
        },
        'body': json.dumps(body)
    }
