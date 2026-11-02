from dataclasses import fields, is_dataclass
from datetime import datetime
from typing import Any, Dict, List

from espn_api.basketball import League, Team
from espn_api.basketball.box_score import H2HCategoryBoxScore as BoxScore

from cat5 import EmptyStart, Matchup, MatchupPeriod

from . import struct


class Processor:
    def __init__(self, league: League, box_scores: List[BoxScore]):
        self.league = league
        self.box_scores = box_scores
        self.matchup_period = MatchupPeriod(league)
        self.now = datetime.now()
        self.n_iter = 2000

    def build(self) -> struct.Cat5Instance:
        matchups = self.get_matchups()
        teams = self.get_teams()
        players = self.get_players()
        instance = struct.Cat5Instance(
            leagueId=str(self.league.league_id),
            year=self.league.year,
            matchupPeriod=self.matchup_period.period,
            updateTimestamp=int(self.now.timestamp()),
            maxGP=self.matchup_period.max_gp,
            matchups=matchups,
            teams=teams,
            players=players,
        )
        instance_rounded: struct.Cat5Instance = round_floats(instance, 4)
        return instance_rounded

    def get_matchups(self) -> List[struct.Matchup]:
        matchups: List[struct.Matchup] = []
        for box in self.box_scores:
            if not box.away_team:
                print(f'{box.home_team} has a BYE')
                continue

            matchup = Matchup(box, self.matchup_period, self.now)
            home_team: Team = box.home_team
            away_team: Team = box.away_team

            matchup.home_lineup.set_probable()
            matchup.away_lineup.set_probable()
            model = matchup.get_model()
            default_forecast = struct.Forecast(
                win=model.predict_win(),
                catWin=model.predict_cats(),
                tie=model.predict_outcome().tie,
                catTie={cat: result.tie for cat,
                        result in model.predict_cat_outcomes().items()},
            )

            matchup.home_lineup.set_probable()
            matchup.away_lineup.set_probable()
            home_player_values = matchup.optimize_home_lineup(self.n_iter)
            model = matchup.get_model()
            home_opt_forecast = struct.Forecast(
                win=model.predict_win(),
                catWin=model.predict_cats(),
                tie=model.predict_outcome().tie,
                catTie={cat: result.tie for cat,
                        result in model.predict_cat_outcomes().items()},
            )

            matchup.home_lineup.set_probable()
            matchup.away_lineup.set_probable()
            away_player_values = matchup.optimize_away_lineup(self.n_iter)
            model = matchup.get_model()
            away_opt_forecast = struct.Forecast(
                win=model.predict_win(),
                catWin=model.predict_cats(),
                tie=model.predict_outcome().tie,
                catTie={cat: result.tie for cat,
                        result in model.predict_cat_outcomes().items()},
            )

            matchups.append(
                struct.Matchup(
                    desc=(
                        f'({self.matchup_period.period}) '
                        f'{away_team.team_abbrev} @ {home_team.team_abbrev}'
                    ),
                    homeTeam=str(home_team.team_id),
                    awayTeam=str(away_team.team_id),
                    forecasts=struct.MatchupForecasts(
                        default=default_forecast,
                        homeOptimized=home_opt_forecast,
                        awayOptimized=away_opt_forecast,
                    ),
                    homePlayerValue=[
                        struct.PlayerValue(str(pv.player.playerId), pv.value,
                                           pv.scheduled, pv.eligible, pv.recommended,
                                           pv.decision, pv.starts)
                        for pv in home_player_values
                    ],
                    awayPlayerValue=[
                        struct.PlayerValue(str(pv.player.playerId), pv.value,
                                           pv.scheduled, pv.eligible, pv.recommended,
                                           pv.decision, pv.starts)
                        for pv in away_player_values
                    ],
                    homeGP=int(box.home_stats['GP']['value']),
                    awayGP=int(box.away_stats['GP']['value']),
                    homeLineup=matchup.home_lineup.optimization,
                    awayLineup=matchup.away_lineup.optimization,
                )
            )

        return matchups

    def get_teams(self) -> Dict[str, struct.Team]:
        teams: Dict[str, struct.Team] = {}
        for team in self.league.teams:
            teams[str(team.team_id)] = struct.Team(
                abbrev=team.team_abbrev,
                name=team.team_name,
                manager=(
                    f'{team.owners[0]["firstName"]} '
                    f'{team.owners[0]["lastName"]}'
                ),
                logoUrl=team.logo_url,
                record=f'{team.wins}-{team.losses}-{team.ties}',
                seed=team.standing,
            )
        return dict(sorted(teams.items(), key=lambda x: int(x[0])))

    def get_players(self) -> Dict[str, struct.Player]:
        players: Dict[str, struct.Player] = {}
        empty_player = EmptyStart.EmptyPlayer()
        for team in self.league.teams:
            for player in [*team.roster, empty_player]:
                estimated_return = getattr(player, 'estimated_return', None)
                players[str(player.playerId)] = struct.Player(
                    name=player.name,
                    pos=player.position,
                    proTeam=player.proTeam,
                    injuryStatus=getattr(player, 'injuryStatus', '') or '',
                    estimatedReturn=estimated_return.isoformat() if estimated_return else None,
                    injuryNote=getattr(player, 'injury_note', ''),
                    injured=getattr(player, 'injured', False),
                )
        return dict(sorted(players.items(), key=lambda x: int(x[0])))


def round_floats(obj: Any, ndigits: int) -> Any:
    if is_dataclass(obj):
        for field in fields(obj):
            value = getattr(obj, field.name)
            setattr(obj, field.name, round_floats(value, ndigits))
    elif isinstance(obj, list):
        return [round_floats(item, ndigits) for item in obj]
    elif isinstance(obj, dict):
        return {k: round_floats(v, ndigits) for k, v in obj.items()}
    elif isinstance(obj, float):
        return round(obj, ndigits)
    return obj
