from collections import defaultdict
from datetime import datetime
from typing import Any, List, NamedTuple, Tuple

import numpy as np
from espn_api.basketball import Player, Team
from espn_api.basketball.box_score import H2HCategoryBoxScore as BoxScore

from .model import Model
from .period import MatchupPeriod
from .start import PlayerStart


class Matchup:
    def __init__(
        self,
        box: BoxScore,
        matchup_period: MatchupPeriod,
        from_date: datetime = datetime.now(),
    ):
        self.box = box
        self.matchup_period = matchup_period
        self.from_date = from_date

        self.home_lineup = Lineup(box.home_team, self)
        self.away_lineup = Lineup(box.away_team, self)

    def __repr__(self):
        return f'Cat5Matchup(H:{self.box.home_team}, A:{self.box.away_team})'

    def get_model(self) -> Model:
        return Model(self.box, self.home_lineup.lineup, self.away_lineup.lineup)

    def optimize_home_lineup(self, n=1000) -> List[Tuple[Player, float]]:
        return self._optimize_lineup(use_home=True, n=n)

    def optimize_away_lineup(self, n=1000) -> List[Tuple[Player, float]]:
        return self._optimize_lineup(use_home=False, n=n)

    def _optimize_lineup(self, use_home: bool, n: int) -> List[Tuple[Player, float]]:
        lineup = self.home_lineup if use_home else self.away_lineup

        best_lineup: List[PlayerStart] = []
        best_win_p = -1.0
        player_id_map: defaultdict[int, Player] = defaultdict(Player)
        player_win_p: defaultdict[int, float] = defaultdict(float)
        player_count: defaultdict[int, int] = defaultdict(int)

        for _ in range(n):
            lineup.set_randomly(min_w=20, max_w=80)
            win_p = self.get_model().predict_win()
            for player_start in lineup.lineup:
                pid = player_start.player.playerId
                player_id_map[pid] = player_start.player
                player_win_p[pid] += win_p
                player_count[pid] += 1
            if win_p > best_win_p:
                best_win_p = win_p
                best_lineup = lineup.lineup

        player_values = {
            pid: player_win_p[pid] / player_count[pid]
            for pid in player_id_map
        }
        lineup.lineup = sorted(
            best_lineup,
            key=lambda p: player_values[p.player.playerId],
            reverse=True,
        )
        return sorted(
            [(player_id_map[pid], pv) for pid, pv in player_values.items()],
            key=lambda x: x[1],
            reverse=True,
        )


class Lineup:
    class EligibleStart(NamedTuple):
        player_start: PlayerStart
        std_weight: float
        probable_weight: float

    def __init__(self, team: Team, matchup: Matchup):
        self.team = team
        self.lineup: List[PlayerStart] = []
        box_home_team: Team = matchup.box.home_team
        box_away_team: Team = matchup.box.away_team
        if team.team_id == box_home_team.team_id:
            box_stats = matchup.box.home_stats
            box_lineup = matchup.box.home_lineup
        elif team.team_id == box_away_team.team_id:
            box_stats = matchup.box.away_stats
            box_lineup = matchup.box.away_lineup
        else:
            raise ValueError('team not present in matchup')

        player_gp = {
            player.playerId: player.stats['0']['total']['GP']
            for player in box_lineup
        }

        start_list = [
            PlayerStart(player, gid)
            for player in team.roster
            for gid, game in player.schedule.items()
            if gid in matchup.matchup_period.game_day_ids
            and game['date'] >= matchup.from_date
            and not player.injured
            and player.injuryStatus != 'SUSPENSION'
        ]

        self.eligible_starts: List[Lineup.EligibleStart] = [
            self.EligibleStart(
                start,
                start.player.percent_owned,
                probable_start_score(
                    start.player.percent_owned,
                    player_gp.get(start.player.playerId, 0),
                ),
            )
            for start in start_list
        ]

        self.remaining_gp = int(
            matchup.matchup_period.max_gp -
            box_stats['GP']['value']
        )
        self.set_default()

    def __repr__(self):
        return f'Lineup({[str(s) for s in self.lineup]})'

    def set_default(self) -> None:
        sorted_starts = [
            es.player_start
            for es in sorted(
                self.eligible_starts,
                key=lambda x: x.std_weight,
                reverse=True,
            )
        ]
        self.lineup = sorted_starts[:self.remaining_gp]

    def set_probable(self) -> None:
        sorted_starts = [
            es.player_start
            for es in sorted(
                self.eligible_starts,
                key=lambda x: x.probable_weight,
                reverse=True,
            )
        ]
        self.lineup = sorted_starts[:self.remaining_gp]

    def set_randomly(self, probable=False, min_w=0.0, max_w=100.0) -> None:
        if len(self.eligible_starts) <= self.remaining_gp:
            self.lineup = [es.player_start for es in self.eligible_starts]
            return

        bounded_weights = [
            max(min_w, min(max_w, es.probable_weight if probable else es.std_weight))
            for es in self.eligible_starts
        ]
        self.lineup = random_draw(
            [es.player_start for es in self.eligible_starts],
            self.remaining_gp,
            bounded_weights,
        )


def probable_start_score(percent_owned: float, gp: int) -> float:
    return (percent_owned + 100*gp) / (1 + gp)


def random_draw(arr: List[Any], n: int, w_arr: List[float]) -> List[Any]:
    total = sum(w_arr)
    p_arr = [w / total for w in w_arr]
    return list(np.random.choice(a=arr, size=n, replace=False, p=p_arr))
