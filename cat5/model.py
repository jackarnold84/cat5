from functools import cache
from typing import Dict, Iterable, List

import numpy as np
from espn_api.basketball.box_score import H2HCategoryBoxScore as BoxScore
from scipy.stats import norm, skellam

from .poibin import PoiBin
from .start import PlayerStart

scored_cats = ['FG%', 'FT%', '3PM', 'REB', 'AST', 'STL', 'BLK', 'TO', 'PTS']
count_cats = ['3PM', 'REB', 'AST', 'STL', 'BLK', 'TO', 'PTS']
ratio_cats = ['FG%', 'FT%']
negative_cats = ['TO']
ratio_to_count_cats = {
    'FG%': ('FGA', 'FGM'),
    'FT%': ('FTA', 'FTM'),
}


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
    def predict_cat(self, cat: str) -> float:
        """
        Give the probability that the home team will win the specified
        category in the matchup
        """
        if cat in count_cats:
            p = self._predict_count_cat(cat)
        elif cat in ratio_cats:
            p = self._predict_ratio_cat(cat)
        else:
            raise ValueError(f'Invalid category: {cat}')

        p = float(p)
        return 1 - p if cat in negative_cats else p

    def predict_cats(self) -> Dict[str, float]:
        """
        Returns a dictionary with predict_cat() results for each category
        """
        return {cat: self.predict_cat(cat) for cat in scored_cats}

    def predict_win(self) -> float:
        """
        Give the probability that the home team will win the matchup by
        winning 5+ of the 9 scored categories
        """
        cat_probs = [self.predict_cat(cat) for cat in scored_cats]
        poi_bin = PoiBin(cat_probs)
        return max(float(1 - poi_bin.cdf(4)), 0.0)

    def _predict_count_cat(self, cat: str) -> float:
        """
        Player count categories are assumed to follow a Poisson
        distribution. The total difference is calculated using
        a Skellam distribution.
        """
        home_curr_count = self.box.home_stats[cat]['value']
        away_curr_count = self.box.away_stats[cat]['value']
        diff = home_curr_count - away_curr_count

        home_starts = get_proj_list(self.home_starts, cat)
        away_starts = get_proj_list(self.away_starts, cat)

        mu_home = sum(home_starts)
        mu_away = sum(away_starts)

        if mu_home > 10 and mu_away > 10:
            return 1 - skellam_cdf_approx(-diff, mu_home, mu_away)
        else:
            return 1 - skellam_cdf_continuous(-diff, mu_home, mu_away)

    def _predict_ratio_cat(self, cat: str) -> float:
        """
        Calculated using the sum of player ratios weigted by the
        proportion of attempts. Individual player ratios assume a
        binomial distribution approximated by a normal distribution.
        """
        att_cat, make_cat = ratio_to_count_cats[cat]

        home_curr_att = self.box.home_stats[att_cat]['value']
        away_curr_att = self.box.away_stats[att_cat]['value']
        home_curr_make = self.box.home_stats[make_cat]['value']
        away_curr_make = self.box.away_stats[make_cat]['value']

        home_starts_att = get_proj_list(self.home_starts, att_cat)
        away_starts_att = get_proj_list(self.away_starts, att_cat)
        home_starts_ratio = get_proj_list(self.home_starts, cat)
        away_starts_ratio = get_proj_list(self.away_starts, cat)

        home_att_total = home_curr_att + sum(home_starts_att)
        away_att_total = away_curr_att + sum(away_starts_att)

        home_curr_score = home_curr_make / home_att_total
        away_curr_score = away_curr_make / away_att_total
        diff = home_curr_score - away_curr_score

        mu_home = sum([
            (att / home_att_total) * ratio
            for att, ratio in zip(home_starts_att, home_starts_ratio)
        ])
        mu_away = sum([
            (att / away_att_total) * ratio
            for att, ratio in zip(away_starts_att, away_starts_ratio)
        ])
        var_home = sum([
            att * ratio * (1 - ratio)
            for att, ratio in zip(home_starts_att, home_starts_ratio)
        ]) / (home_att_total ** 2)
        var_away = sum([
            att * ratio * (1 - ratio)
            for att, ratio in zip(away_starts_att, away_starts_ratio)
        ]) / (away_att_total ** 2)

        return 1 - norm.cdf(
            -diff, mu_home - mu_away, max(np.sqrt(var_home + var_away), 1e-9)
        )


def get_proj_list(starts: Iterable[PlayerStart], cat: str) -> List[float]:
    return [start.projection(cat) for start in starts]


def skellam_cdf_continuous(k: float, mu1: float, mu2: float) -> float:
    """
    Breaks ties (i.e. x = k) with 50-50 probability
    """
    mu1 = max(mu1, 1e-9)
    mu2 = max(mu2, 1e-9)
    cdf_val = skellam.cdf(k, mu1, mu2)
    pmf_val = skellam.pmf(k, mu1, mu2)
    return cdf_val - 0.5 * pmf_val


def skellam_cdf_approx(k: float, mu1: float, mu2: float) -> float:
    return norm.cdf(k, mu1 - mu2, max(np.sqrt(mu1 + mu2), 1e-9))
