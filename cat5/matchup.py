from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, NamedTuple

import numpy as np
from espn_api.basketball import Player, Team
from espn_api.basketball.box_score import H2HCategoryBoxScore as BoxScore

from .model import Model
from .period import MatchupPeriod
from .start import PlayerStart


class Matchup:
    @dataclass
    class PlayerValue:
        player: Player
        value: float
        scheduled: int = 0
        eligible: int = 0
        recommended: int = 0
        decision: str = 'Consider'
        starts: List[dict] = field(default_factory=list)

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

    def optimize_home_lineup(self, n=1000) -> List[PlayerValue]:
        return self._optimize_lineup(use_home=True, n=n)

    def optimize_away_lineup(self, n=1000) -> List[PlayerValue]:
        return self._optimize_lineup(use_home=False, n=n)

    def _optimize_lineup(self, use_home: bool, n: int) -> List[PlayerValue]:
        """Search start counts, then measure paired single-start alternatives.

        The opponent stays fixed. Values are signed win-probability changes,
        not ownership scores or averages over unrelated random teammates.
        """
        lineup = self.home_lineup if use_home else self.away_lineup
        candidates = [es.player_start for es in lineup.eligible_starts]
        scores: Dict[frozenset, float] = {}
        by_count: Dict[int, float] = {}

        def score(starts):
            key = frozenset(starts)
            if key not in scores:
                lineup.lineup = list(starts)
                result = self.get_model().predict_outcome()
                scores[key] = result.home if use_home else result.away
            value = scores[key]
            count = len(starts)
            by_count[count] = max(by_count.get(count, 0.0), value)
            return value

        best = list(lineup.lineup)
        best_p = score(best)

        def consider(starts):
            nonlocal best, best_p
            value = score(starts)
            # Prefer fewer starts on exact ties: no benefit to spending a game.
            if value > best_p + 1e-12 or (abs(value - best_p) <= 1e-12
                                        and len(starts) < len(best)):
                best, best_p = list(starts), value

        consider([])
        # Search every feasible count, including multiple unused slots.
        ranked = sorted(lineup.eligible_starts,
                        key=lambda es: es.probable_weight, reverse=True)
        for count in range(1, min(lineup.remaining_gp, len(candidates)) + 1):
            consider([es.player_start for es in ranked[:count]])
        for _ in range(n):
            lineup.set_randomly(min_w=10, max_w=95)
            consider(lineup.lineup)

        # Polish the sampled solution with add/remove/swap neighbors. Bounded
        # passes keep processor cost predictable; this is not an exhaustive solve.
        def alternatives(start, chosen):
            if start in chosen:
                rest = [s for s in chosen if s is not start]
                return [rest] + [rest + [s] for s in candidates if s not in chosen]
            added = [chosen + [start]] if len(chosen) < lineup.remaining_gp else []
            return added + [[s for s in chosen if s is not removed] + [start]
                            for removed in chosen]

        for _ in range(2):
            before = frozenset(best)
            for start in candidates:
                for option in alternatives(start, best):
                    consider(option)
            if frozenset(best) == before:
                break

        # Freeze the context so every reported comparison uses the same lineup.
        chosen, chosen_p = list(best), best_p
        grouped = defaultdict(list)
        for start in candidates:
            options = alternatives(start, chosen)
            alternative_p = max((score(option) for option in options), default=chosen_p)
            impact = (chosen_p - alternative_p if start in chosen
                      else alternative_p - chosen_p)
            grouped[start.player.playerId].append({
                'date': start.game_datetime.isoformat(),
                'selected': start in chosen,
                'impact': impact,
            })

        values = []
        for player in lineup.team.roster:
            starts = sorted(grouped[player.playerId], key=lambda s: s['date'])
            eligible = len(starts)
            selected = sum(s['selected'] for s in starts)
            scheduled = len(lineup.scheduled_starts[player.playerId])
            # 0.2 percentage points is a display threshold, not confidence.
            if not scheduled:
                decision = 'No games'
            elif not eligible:
                decision = 'Unavailable'
            elif not lineup.remaining_gp:
                decision = 'Cap reached'
            elif selected == eligible and all(s['impact'] > .002 for s in starts):
                decision = 'Start'
            elif not selected and all(s['impact'] < -.002 for s in starts):
                decision = 'Sit'
            else:
                decision = 'Consider'
            values.append(self.PlayerValue(
                player, sum(s['impact'] for s in starts) / eligible if eligible else 0.0,
                scheduled, eligible, selected, decision, starts))
        lineup.lineup = chosen
        lineup.optimization = {
            'remaining': lineup.remaining_gp,
            'recommended': len(chosen),
            'unused': max(0, lineup.remaining_gp - len(chosen)),
            'available': len(candidates),
            'winByStarts': [{'starts': count, 'win': value}
                            for count, value in sorted(by_count.items())],
        }
        return sorted(values, key=lambda v: (v.value, v.player.percent_owned), reverse=True)


class Lineup:
    class EligibleStart(NamedTuple):
        player_start: PlayerStart
        std_weight: float
        probable_weight: float

    def __init__(self, team: Team, matchup: Matchup):
        self.team = team
        self.optimization: dict = {}
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

        self.scheduled_starts = {
            player.playerId: [PlayerStart(player, gid)
                              for gid, game in player.schedule.items()
                              if gid in matchup.matchup_period.game_day_ids
                              and game['date'] >= matchup.from_date]
            for player in team.roster
        }
        start_list = [start for player in team.roster
                      for start in self.scheduled_starts[player.playerId]
                      if start_is_available(player, start.game_date, matchup.from_date.date())]

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

        self.remaining_gp = max(0, int(
            matchup.matchup_period.max_gp - box_stats['GP']['value']))
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
        count = int(np.random.randint(0, min(self.remaining_gp, len(self.eligible_starts)) + 1))
        bounded_weights = [
            max(min_w, min(max_w, es.probable_weight if probable else es.std_weight))
            for es in self.eligible_starts
        ]
        self.lineup = random_draw(
            [es.player_start for es in self.eligible_starts], count, bounded_weights)


def start_is_available(player, game_date, as_of):
    if player.injuryStatus == 'SUSPENSION':
        return False
    if not player.injured:
        return True
    estimate = getattr(player, 'estimated_return', None)
    # Past/today estimates must not overrule a still-injured roster status.
    return estimate is not None and estimate > as_of and game_date >= estimate


def probable_start_score(percent_owned: float, gp: int) -> float:
    return (percent_owned + 100*gp) / (1 + gp)


def random_draw(arr: List[Any], n: int, w_arr: List[float]) -> List[Any]:
    if n <= 0 or not arr:
        return []
    positive = [item for item, weight in zip(arr, w_arr) if weight > 0]
    if len(positive) < n:
        unweighted = [item for item, weight in zip(arr, w_arr) if weight <= 0]
        return positive + list(np.random.choice(
            a=unweighted, size=n - len(positive), replace=False))
    total = sum(w_arr)
    p_arr = [w / total for w in w_arr] if total else [1 / len(arr)] * len(arr)
    return list(np.random.choice(a=arr, size=n, replace=False, p=p_arr))
