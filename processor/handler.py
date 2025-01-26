from dataclasses import asdict
from typing import Any, Dict, Optional

from espn_api.basketball import League
from pydantic import ValidationError
from pydantic.dataclasses import dataclass

from .db import DBWriter
from .processor import Processor

IN_PROGRESS = 'IN_PROGRESS'
SUCCESS = 'SUCCESS'
ERROR = 'ERROR'


@dataclass
class LambdaPayload:
    tag: str
    leagueId: str
    year: int
    iter: Optional[int] = None


@dataclass
class LambdaRespose:
    status: str
    msg: Optional[str] = ''
    tag: Optional[str] = ''


def lambda_handler(event: Dict[str, Any], _) -> Dict[str, Any]:
    try:
        return handler(event, _)
    except Exception as e:
        print('----- unexpected lambda error -----')
        print(e)
        print('-----------------------------------')
        raise e


def handler(event: Dict[str, Any], _) -> Dict[str, Any]:
    resp = LambdaRespose(IN_PROGRESS)
    db = DBWriter()

    # read event payload
    print('--> parsing event')
    payload = event
    if event.get('detail-type') == 'Scheduled Event':
        payload = event.get('detail', {})

    try:
        lambda_payload = LambdaPayload(**payload)
        resp.tag = lambda_payload.tag
    except ValidationError as e:
        resp.status = ERROR
        resp.msg = f'invalid payload: {e}'
        return asdict(resp)

    # fetch espn league
    print('--> fetching league from espn')
    league = League(lambda_payload.leagueId, lambda_payload.year)
    box_scores = league.box_scores()

    # process cat5 data
    print('--> running cat5 processor')
    processor = Processor(league, box_scores)
    if lambda_payload.iter:
        processor.n_iter = lambda_payload.iter
    cat5_instance = processor.build()
    cat5_instance_dict = asdict(cat5_instance)

    # write to db
    print('--> saving update to db')
    db.write(lambda_payload.tag, cat5_instance_dict)

    resp.status = SUCCESS
    resp.msg = 'update saved to db'
    return asdict(resp)
