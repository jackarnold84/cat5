
from datetime import date, datetime
from functools import cache

from espn_api.basketball import Player

cat_to_weight = {
    'FT%': 25,
    'FG%': 20,
    'STL': 20,
    'BLK': 20,
}


class PlayerStart:
    def __init__(self, player: Player, game_day_id: str):
        self.player = player
        self.game_day_id = game_day_id
        self.game_datetime: datetime = player.schedule[game_day_id]['date']
        self.game_date: date = self.game_datetime.date()
        self.injured = self.player.injured

    def __repr__(self) -> str:
        return f'Start({self.player}, Date({self.game_date}))'

    @cache
    def projection(self, cat: str) -> float:
        stats = self.player.stats
        # TODO: weight with last 7/15/30 stats
        preseason_stats = stats[f'{self.player.year}_projected']
        actual_stats = stats[f'{self.player.year}_total']

        preseason = preseason_stats['avg'].get(cat, 0)
        actual = actual_stats['avg'].get(cat, 0)
        actual_gp = actual_stats['total']['GP']

        a = cat_to_weight.get(cat, 15)
        d = 3
        w_pre = a**d
        w_act = actual_gp**d
        return (w_pre * preseason + w_act * actual) / (w_pre + w_act)
