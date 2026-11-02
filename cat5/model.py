from functools import cache
from typing import Dict, Iterable, List, NamedTuple

import numpy as np
from espn_api.basketball.box_score import H2HCategoryBoxScore as BoxScore
from scipy.stats import norm, poisson, skellam

from .start import PlayerStart

scored_cats = ['FG%', 'FT%', '3PM', 'REB', 'AST', 'STL', 'BLK', 'TO', 'PTS']
count_cats = ['3PM', 'REB', 'AST', 'STL', 'BLK', 'TO', 'PTS']
ratio_cats = ['FG%', 'FT%']
negative_cats = ['TO']
ratio_to_count_cats = {
    'FG%': ('FGA', 'FGM'),
    'FT%': ('FTA', 'FTM'),
}


class Outcome(NamedTuple):
    home: float
    away: float
    tie: float


def outcome(home: float, away: float, tie: float) -> Outcome:
    """Remove floating-point drift while retaining small tail probabilities."""
    values = [max(0.0, min(1.0, float(p))) for p in (home, away, tie)]
    total = sum(values)
    return Outcome(*(p / total for p in values))


def settled_outcome(home: float, away: float) -> Outcome:
    return Outcome(float(home > away), float(home < away), float(home == away))


class Model:
    def __init__(
        self,
        box: BoxScore,
        home_starts: Iterable[PlayerStart],
        away_starts: Iterable[PlayerStart],
    ):
        self.box = box
        self.home_starts = tuple(home_starts)
        self.away_starts = tuple(away_starts)

    @cache
    def predict_cat_outcome(self, cat: str) -> Outcome:
        """Return strict home/away win and tie probabilities for a category."""
        if cat in count_cats:
            result = self._predict_count_cat(cat)
        elif cat in ratio_cats:
            result = self._predict_ratio_cat(cat)
        else:
            raise ValueError(f'Invalid category: {cat}')
        if cat in negative_cats:
            return Outcome(result.away, result.home, result.tie)
        return result

    def predict_cat(self, cat: str) -> float:
        return self.predict_cat_outcome(cat).home

    def predict_cats(self) -> Dict[str, float]:
        return {cat: self.predict_cat(cat) for cat in scored_cats}

    def predict_cat_outcomes(self) -> Dict[str, Outcome]:
        return {cat: self.predict_cat_outcome(cat) for cat in scored_cats}

    @cache
    def predict_outcome(self) -> Outcome:
        """Convolve independent category outcomes over the category-win margin."""
        margins = np.array([1.0])
        for cat in scored_cats:
            result = self.predict_cat_outcome(cat)
            margins = np.convolve(
                margins, [result.away, result.tie, result.home])
        center = len(scored_cats)
        return outcome(sum(margins[center + 1:]), sum(margins[:center]), margins[center])

    def predict_win(self) -> float:
        """Probability that home wins more categories than away."""
        return self.predict_outcome().home

    def _predict_count_cat(self, cat: str) -> Outcome:
        """Independent Poisson totals give a discrete Skellam difference."""
        diff = self.box.home_stats[cat]['value'] - \
            self.box.away_stats[cat]['value']
        mu_home = sum(get_proj_list(self.home_starts, cat))
        mu_away = sum(get_proj_list(self.away_starts, cat))

        if mu_home == 0 and mu_away == 0:
            return settled_outcome(diff, 0)
        if mu_away == 0:
            return outcome(poisson.sf(-diff, mu_home),
                           poisson.cdf(-diff - 1, mu_home),
                           poisson.pmf(-diff, mu_home))
        if mu_home == 0:
            return outcome(poisson.cdf(diff - 1, mu_away),
                           poisson.sf(diff, mu_away),
                           poisson.pmf(diff, mu_away))
        return outcome(skellam.sf(-diff, mu_home, mu_away),
                       skellam.cdf(-diff - 1, mu_home, mu_away),
                       skellam.pmf(-diff, mu_home, mu_away))

    def _predict_ratio_cat(self, cat: str) -> Outcome:
        """Keep the weighted normal approximation for uncertain shooting.

        Continuous outcomes have no tie mass. Deterministic results are compared
        directly, including completed ratios with different attempt totals.
        """
        att_cat, make_cat = ratio_to_count_cats[cat]
        totals = []
        makes = []
        variances = []
        for stats, starts in ((self.box.home_stats, self.home_starts),
                              (self.box.away_stats, self.away_starts)):
            attempts = get_proj_list(starts, att_cat)
            ratios = get_proj_list(starts, cat)
            total = stats[att_cat]['value'] + sum(attempts)
            make = stats[make_cat]['value'] + sum(
                att * ratio for att, ratio in zip(attempts, ratios)
            )
            totals.append(total)
            makes.append(make)
            variances.append(sum(
                att * ratio * (1 - ratio) for att, ratio in zip(attempts, ratios)
            ) / total ** 2 if total else 0.0)

        # A team with no attempts has a shooting percentage of zero.
        denominators = [total if total else 1 for total in totals]
        variance = sum(variances)
        if variance == 0:
            return settled_outcome(makes[0] * denominators[1],
                                   makes[1] * denominators[0])
        diff = makes[0] / denominators[0] - makes[1] / denominators[1]
        std = np.sqrt(variance)
        return outcome(norm.sf(0, diff, std), norm.cdf(0, diff, std), 0.0)


def get_proj_list(starts: Iterable[PlayerStart], cat: str) -> List[float]:
    return [start.projection(cat) for start in starts]
