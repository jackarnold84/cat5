from typing import Dict, List

from pydantic.dataclasses import dataclass


@dataclass
class Player:
    name: str
    pos: str
    proTeam: str


@dataclass
class Team:
    abbrev: str
    name: str
    manager: str
    logoUrl: str
    record: str
    seed: int


@dataclass
class Forecast:
    win: float
    catWin: Dict[str, float]


@dataclass
class MatchupForecasts:
    default: Forecast
    homeOptimized: Forecast
    awayOptimized: Forecast


@dataclass
class PlayerValue:
    player: str
    value: float


@dataclass
class Matchup:
    desc: str
    homeTeam: str
    awayTeam: str
    forecasts: MatchupForecasts
    homePlayerValue: List[PlayerValue]
    awayPlayerValue: List[PlayerValue]
    homeGP: int
    awayGP: int


@dataclass
class Cat5Instance:
    leagueId: str
    matchupPeriod: int
    maxGP: int
    matchups: List[Matchup]
    teams: Dict[str, Team]
    players: Dict[str, Player]
