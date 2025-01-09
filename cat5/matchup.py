from collections import defaultdict
from datetime import datetime
from functools import lru_cache
from typing import Dict, List, Tuple

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
        return self._optimize_lineup(self.home_lineup, n)

    def optimize_away_lineup(self, n=1000) -> List[Tuple[Player, float]]:
        return self._optimize_lineup(self.away_lineup, n)

    def _optimize_lineup(self, use_home: bool, n: int) -> List[Tuple[Player, float]]:
        lineup = self.home_lineup if use_home else self.away_lineup

        best_lineup: List[PlayerStart] = []
        best_win_p = -1.0
        player_id_map: defaultdict[int, Player] = defaultdict(Player)
        player_win_p: defaultdict[int, float] = defaultdict(float)
        player_count: defaultdict[int, int] = defaultdict(int)

        for _ in range(n):
            lineup.set_randomly(min_weight=0.1)
            win_p = self.get_model().predict_win()
            for player_start in lineup.lineup:
                pid = player_start.player.playerId
                player_id_map[pid] = player_start.player
                player_win_p[pid] += win_p
                player_count[pid] += 1
            if win_p > best_win_p:
                best_win_p = win_p
                best_lineup = lineup.lineup.copy()

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
    def __init__(self, team: Team, matchup: Matchup):
        self.team = team
        self.lineup: List[PlayerStart] = []
        if team.team_id == matchup.box.home_team.team_id:
            box_stats = matchup.box.home_stats
            box_lineup = matchup.box.home_lineup
        elif team.team_id == matchup.box.away_team.team_id:
            box_stats = matchup.box.away_stats
            box_lineup = matchup.box.away_lineup
        else:
            raise ValueError('team not present in matchup')

        self.eligible_starts: List[PlayerStart] = []
        for player in team.roster:
            for gid, game in player.schedule.items():
                if gid in matchup.matchup_period.game_day_ids \
                        and game['date'] >= matchup.from_date \
                        and not player.injured \
                        and player.injuryStatus != 'SUSPENSION':
                    self.eligible_starts.append(PlayerStart(player, gid))

        self._es_weights: Tuple[float, ...] = tuple([
            p.player.percent_started for p in self.eligible_starts
        ])

        matchup.box.home_lineup
        self.remaining_gp = int(
            matchup.matchup_period.max_gp -
            box_stats['GP']['value']
        )

        self._player_gp: Dict[int, int] = {
            player.playerId: player.stats['0']['total']['GP']
            for player in box_lineup
        }

        self.set_default()

    def __repr__(self):
        return f'Lineup({[str(s) for s in self.lineup]})'

    def set_default(self) -> None:
        sorted_starts = sorted(
            self.eligible_starts,
            key=lambda p: p.player.percent_started,
            reverse=True
        )
        self.lineup = sorted_starts[:self.remaining_gp]

    def set_probable(self) -> None:
        sorted_starts = sorted(
            self.eligible_starts,
            key=lambda p: self._probable_start_score(p.player),
            reverse=True
        )
        self.lineup = sorted_starts[:self.remaining_gp]

    def set_randomly(self, min_weight=0.0) -> None:
        if len(self.eligible_starts) <= self.remaining_gp:
            self.lineup = self.eligible_starts
            return

        self.lineup = np.random.choice(
            self.eligible_starts,
            size=self.remaining_gp,
            replace=False,
            p=normalize_weights(self._es_weights, min_weight),
        )

    def _probable_start_score(self, player: Player) -> float:
        n_starts = self._player_gp.get(player.playerId, 0)
        return (player.percent_started + n_starts) / (1 + n_starts)


@lru_cache(maxsize=1000)
def normalize_weights(weights: Tuple[float, ...], min_weight=0.0) -> Tuple[float, ...]:
    if min_weight > 0.0:
        weights = [max(min_weight, w) for w in weights]
    total = sum(weights)
    return tuple([w / total for w in weights])
