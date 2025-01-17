import time
from typing import Any, Dict, NamedTuple

from aws_lambda_powertools.event_handler import (APIGatewayRestResolver,
                                                 CORSConfig)
from aws_lambda_powertools.utilities.typing import LambdaContext

from .db import DBReader


class CacheItem(NamedTuple):
    data: Dict[str, Any]
    ttl: float


CACHE_TTL = 300  # 5 minutes
cache: Dict[str, CacheItem] = {}
db = DBReader()

cors_config = CORSConfig(allow_origin='*')
app = APIGatewayRestResolver(cors=cors_config)


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)


@app.get('/cat5/data/<tag>')
def get_data(tag: str):
    api_event = app.current_event
    cache_param = api_event.get_query_string_value('cache', '')

    if tag in cache and cache_param != 'none':
        item = cache[tag]
        if item.ttl > time.time():
            return item.data, 200
        else:
            del cache[tag]

    try:
        data = db.read(tag)
    except (KeyError, FileNotFoundError):
        return {'error': f'tag not found: {tag}'}, 404

    cache[tag] = CacheItem(data, time.time() + CACHE_TTL)
    return data, 200
