
from datetime import date, datetime
from functools import cache
from typing import Dict, List, TypeAlias

from espn_api.basketball import Player

PlayerStats: TypeAlias = Dict[str, Dict[str, Dict[str, float]]]


class PlayerStart:
    def __init__(self, player: Player, game_day_id: str):
        self.player = player
        self.game_day_id = game_day_id
        self.game_datetime: datetime = player.schedule[game_day_id]['date']
        self.game_date: date = self.game_datetime.date()
        self.injured = self.player.injured
        self.ema_window = 30

    def __repr__(self) -> str:
        return f'Start({self.player}, Date({self.game_date}))'

    @cache
    def projection(self, cat: str) -> float:
        player_stats: PlayerStats = self.player.stats
        year = self.player.year
        preseason_avg = player_stats.get(f'{year}_projected', {}) \
            .get('avg', {}).get(cat, 0)

        periods = ['last_7', 'last_15', 'last_30', 'total']
        stats = {
            period: player_stats.get(f'{year}_{period}', {}) for period in periods
        }
        gps = {period: int(stats[period].get('total', {}).get('GP', 0))
               for period in periods}
        avgs = {period: stats[period].get('avg', {}).get(cat, 0)
                for period in periods}
        inside_gps = {
            period: gps[period] - gps[periods[i-1]]
            for i, period in enumerate(periods) if i > 0
        }
        inside_avgs = {
            period: (avgs[period] * gps[period] - avgs[periods[i-1]] * gps[periods[i-1]]) /
            max(inside_gps[period], 1)
            for i, period in enumerate(periods) if i > 0
        }

        ts: List[float] = (
            [avgs['last_7']] * gps['last_7'] +
            [inside_avgs['last_15']] * inside_gps['last_15'] +
            [inside_avgs['last_30']] * inside_gps['last_30'] +
            [avgs['total']] * gps['total']
        )
        ts += [preseason_avg] * (self.ema_window - len(ts))
        ts = list(reversed(ts))
        return ema_next(ts)


def ema_next(ts: List[float]) -> float:
    alpha = 2 / (len(ts) + 1)
    ma = ts[0]
    for t in ts[1:]:
        ma = alpha * t + (1 - alpha) * ma
    return ma
