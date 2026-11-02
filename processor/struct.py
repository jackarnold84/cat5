from dataclasses import field
from typing import Dict, List, Optional

from pydantic.dataclasses import dataclass


@dataclass
class Player:
    name: str
    pos: str
    proTeam: str
    injuryStatus: str = ''
    estimatedReturn: Optional[str] = None
    injuryNote: str = ''
    injured: bool = False


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
    tie: float
    catTie: Dict[str, float]


@dataclass
class MatchupForecasts:
    default: Forecast
    homeOptimized: Forecast
    awayOptimized: Forecast


@dataclass
class PlayerValue:
    player: str
    value: float
    scheduled: int = 0
    eligible: int = 0
    recommended: int = 0
    decision: str = 'Consider'
    starts: List[dict] = field(default_factory=list)


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
    homeLineup: dict = field(default_factory=dict)
    awayLineup: dict = field(default_factory=dict)


@dataclass
class Cat5Instance:
    leagueId: str
    year: int
    matchupPeriod: int
    updateTimestamp: int
    maxGP: int
    matchups: List[Matchup]
    teams: Dict[str, Team]
    players: Dict[str, Player]
