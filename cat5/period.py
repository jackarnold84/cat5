from datetime import datetime
from typing import Set

from espn_api.basketball import League

from .config import matchup_period_start_dates, starts_per_gameday


class MatchupPeriod:
    def __init__(self, league: League):
        self.period: int = league.currentMatchupPeriod
        self.start_date, self.end_date = [
            datetime.strptime(date, '%Y-%m-%d')
            for date in (
                matchup_period_start_dates[league.year][self.period],
                matchup_period_start_dates[league.year][self.period + 1]
            )
        ]
        self.game_day_ids: Set[int] = set()

        for team in league.teams:
            for player in team.roster:
                for gid, game in player.schedule.items():
                    game_date = game['date']
                    if game_date >= self.start_date and game_date < self.end_date:
                        self.game_day_ids.add(gid)

        self.max_gp = len(self.game_day_ids) * starts_per_gameday

    def __repr__(self):
        return (
            f'MatchupPeriod('
            f'period={self.period}, '
            f'start={self.start_date.date()}, '
            f'end={self.end_date.date()}, '
            f'max_gp={self.max_gp}'
            f')'
        )
