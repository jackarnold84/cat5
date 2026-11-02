
from datetime import date, datetime
from functools import cache
from math import isclose, isfinite
from typing import List, Mapping, Optional, Tuple

from espn_api.basketball import Player

SHOOTING_COUNTS = {'FG%': ('FGA', 'FGM'), 'FT%': ('FTA', 'FTM')}


def _nonnegative(value: object) -> Optional[float]:
    """Missing or malformed data is not an observed zero."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except OverflowError:
        return None
    return number if isfinite(number) and number >= 0 else None


def _mapping(value: object) -> Mapping:
    return value if isinstance(value, Mapping) else {}


def _valid_counts(values: Tuple[float, ...]) -> bool:
    # Shooting tuples always contain (attempts, makes).
    return len(values) == 1 or values[1] <= values[0]


def _difference(outer: Tuple[float, ...], inner: Tuple[float, ...]
                ) -> Optional[Tuple[float, ...]]:
    values = tuple(0.0 if a < b and isclose(a, b, rel_tol=1e-9, abs_tol=1e-8)
                   else a - b for a, b in zip(outer, inner))
    if (len(values) == 2 and values[1] > values[0]
            and isclose(values[0], values[1], rel_tol=1e-9, abs_tol=1e-8)):
        values = (values[0], values[0])
    if any(v < 0 for v in values) or not _valid_counts(values):
        return None
    return values


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
        if cat in SHOOTING_COUNTS:
            attempts, makes = self._project_counts(SHOOTING_COUNTS[cat])
            return makes / attempts if attempts else 0.0
        for pair in SHOOTING_COUNTS.values():
            if cat in pair:
                return self._project_counts(pair)[pair.index(cat)]
        return self._project_counts((cat,))[0]

    @cache
    def _project_counts(self, cats: Tuple[str, ...]) -> Tuple[float, ...]:
        """Smooth disjoint game groups, oldest first, without inventing games.

        The order of individual games within each aggregate is unavailable;
        retain the constant-per-game assumption within each group.
        """
        stats = _mapping(self.player.stats)
        windows: List[Tuple[int, Tuple[float, ...]]] = []
        for period in ('total', 'last_30', 'last_15', 'last_7'):
            split = _mapping(stats.get(f'{self.player.year}_{period}'))
            totals = _mapping(split.get('total'))
            avgs = _mapping(split.get('avg'))
            gp = _nonnegative(totals.get('GP'))
            if gp is None or not gp.is_integer() or gp == 0:
                continue
            values = []
            for cat in cats:
                value = _nonnegative(totals.get(cat))
                if value is None:
                    avg = _nonnegative(avgs.get(cat))
                    value = _nonnegative(avg * gp) if avg is not None else None
                if value is None:
                    break
                values.append(value)
            if len(values) != len(cats) or not _valid_counts(tuple(values)):
                continue
            candidate = (int(gp), tuple(values))
            if windows:
                outer_gp, outer = windows[-1]
                residual = _difference(outer, candidate[1])
                if gp > outer_gp or residual is None:
                    continue
                if gp == outer_gp:
                    # No new game group: retain the accepted broader totals.
                    continue
            windows.append(candidate)

        projected = _mapping(stats.get(f'{self.player.year}_projected'))
        projected_avgs = _mapping(projected.get('avg'))
        prior_values = tuple(_nonnegative(projected_avgs.get(cat)) for cat in cats)
        prior = (tuple(float(v) for v in prior_values if v is not None)
                 if all(v is not None for v in prior_values) else ())
        if prior and not _valid_counts(prior):
            prior = ()

        n_games = windows[0][0] if windows else 0
        if not n_games:
            return prior or (0.0,) * len(cats)

        # Keep the minimum span, even when a missing prior cannot pad the series.
        alpha = 2 / (max(self.ema_window, n_games) + 1)
        estimate = prior if prior and n_games < self.ema_window else ()
        for i, (gp, counts) in enumerate(windows):
            inner_gp, inner = windows[i + 1] if i + 1 < len(windows) else (
                0, (0.0,) * len(cats))
            group_gp = gp - inner_gp
            residual = _difference(counts, inner)
            assert residual is not None and group_gp > 0
            rates = tuple(v / group_gp for v in residual)
            if not estimate:
                estimate = rates
            # Closed form of repeated EMA updates; no per-game allocation.
            weight = (1 - alpha) ** group_gp
            estimate = tuple(weight * old + (1 - weight) * rate
                             for old, rate in zip(estimate, rates))
        return estimate


class EmptyStart(PlayerStart):
    class EmptyPlayer(Player):
        def __init__(self):
            self.playerId = 0
            self.name = 'Empty'
            self.position = 'X'
            self.proTeam = 'X'
            self.percent_owned = 0.0

    def __init__(self):
        self.player = self.EmptyPlayer()

    @cache
    def projection(self, _: str) -> float:
        return 0.0


def ema_next(ts: List[float]) -> float:
    if not ts:
        return 0.0
    alpha = 2 / (len(ts) + 1)
    ma = ts[0]
    for t in ts[1:]:
        ma = alpha * t + (1 - alpha) * ma
    return ma
