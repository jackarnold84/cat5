import { Radio, Select, Table } from "antd";
import * as React from "react";
import '../styles/forecast.css';
import { timeSince } from "../utils/display";
import Container from "./common/Container";

const formatP = (p) => {
  if (p === 0) return '0.0%';
  if (p === 1) return '100.0%';
  const percentage = (p * 100).toFixed(1);
  if (percentage === '100.0') {
    return '>99.9%';
  } else if (percentage === '0.0') {
    return '<0.1%';
  }
  return `${percentage}%`;
}

const colorP = (p) => {
  if (typeof p !== 'number' || isNaN(p)) {
    return '';
  }
  const opacity = p / 1.25;
  return `rgba(200, 15, 45, ${opacity})`;
}

const formatImpact = (v) => {
  const points = Number((v * 100).toFixed(2));
  return `${points > 0 ? '+' : ''}${points.toFixed(2)} pp`;
};
const gameDate = (value) => new Date(value).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });

const formatManager = (team) => {
  const [firstName, lastName] = team.manager.split(' ');
  return `${firstName} ${lastName.charAt(0)}`;
}

const formatPlayer = (player) => (
  <><span style={{ fontWeight: '600' }}>{player.pos}</span> {player.name}</>
)


const Forecast = ({ cat5Data }) => {
  // selectors
  const [selectedMatchup, setSelectedMatchup] = React.useState(0);
  const [selectedRadio, setSelectedRadio] = React.useState('default');
  const [selectedForecast, setSelectedForecast] = React.useState('default');
  const [selectedPlayerValue, setSelectedPlayerValue] = React.useState('homePlayerValue');
  const [decisionFilter, setDecisionFilter] = React.useState('All');
  const teams = cat5Data.teams;
  const players = cat5Data.players

  const handleMatchupChange = (value) => {
    setSelectedMatchup(value);
    setSelectedRadio('default');
    setSelectedForecast('default');
    setSelectedPlayerValue('homePlayerValue');
    setDecisionFilter('All');
  };

  const handleRadioChange = (e) => {
    setDecisionFilter('All');
    switch (e.target.value) {
      case 'home':
        setSelectedRadio('home');
        setSelectedPlayerValue('homePlayerValue');
        setSelectedForecast('homeOptimized');
        break;
      case 'away':
        setSelectedRadio('away');
        setSelectedPlayerValue('awayPlayerValue');
        setSelectedForecast('awayOptimized');
        break;
      default:
        setSelectedRadio('default');
        setSelectedForecast('default');
        break;
    }
  };

  const matchup = cat5Data.matchups[selectedMatchup];
  const forecast = matchup.forecasts[selectedForecast];
  const playerValue = matchup[selectedPlayerValue];
  const lineup = matchup[selectedPlayerValue === 'homePlayerValue' ? 'homeLineup' : 'awayLineup'];
  const hasGuidance = Boolean(lineup?.winByStarts);
  const forcedUnused = hasGuidance ? Math.max(0, lineup.remaining - lineup.available) : 0;
  const strategicUnused = hasGuidance ? Math.max(0, lineup.unused - forcedUnused) : 0;
  const fullCount = hasGuidance ? Math.min(lineup.remaining, lineup.available) : 0;
  const fullWin = lineup?.winByStarts?.find(row => row.starts === fullCount)?.win;
  const bestWin = matchup.forecasts[selectedPlayerValue === 'homePlayerValue' ? 'homeOptimized' : 'awayOptimized'];
  const ownWin = selectedPlayerValue === 'homePlayerValue' ? bestWin.win : 1 - bestWin.win - (bestWin.tie ?? 0);


  // cat table setup
  const catTableColumns = [
    {
      title: formatManager(teams[matchup.awayTeam]),
      dataIndex: 'away',
      key: 'away',
      align: 'right',
      render: (_, record) => (
        <>{record.key === 'GP' ? record.away : formatP(record.away)}</>
      ),
      onCell: (record) => ({
        style: {
          backgroundColor: colorP(record.away),
        },
      }),
      width: '35%',
    },
    {
      title: '',
      dataIndex: 'cat',
      key: 'cat',
      align: 'center',
      render: (_, record) => (
        <>
          <div>{record.cat}</div>
          {record.key !== 'GP' && (
            <div className="tie-probability">
              {typeof record.tie === 'number' ? `Tie ${formatP(record.tie)}` : 'Tie unavailable'}
            </div>
          )}
        </>
      ),
      width: '30%',
    },
    {
      title: formatManager(teams[matchup.homeTeam]),
      dataIndex: 'home',
      key: 'home',
      align: 'left',
      render: (_, record) => (
        <>{record.key === 'GP' ? record.home : formatP(record.home)}</>
      ),
      onCell: (record) => ({
        style: {
          backgroundColor: colorP(record.home),
        },
      }),
      width: '35%',
    },
  ];
  const catTableDataSource = Object.entries(forecast.catWin).map(([cat, winP]) => ({
    key: cat,
    cat: cat,
    home: winP,
    tie: forecast.catTie?.[cat],
    away: Math.max(0, Math.min(1, 1 - winP - (forecast.catTie?.[cat] ?? 0))),
  }))
  catTableDataSource.push({
    key: 'OVR',
    cat: 'OVR',
    home: forecast.win,
    tie: forecast.tie,
    away: Math.max(0, Math.min(1, 1 - forecast.win - (forecast.tie ?? 0))),
  })
  catTableDataSource.push({
    key: 'GP',
    cat: 'GP',
    home: `${matchup.homeGP}/${cat5Data.maxGP}`,
    away: `${matchup.awayGP}/${cat5Data.maxGP}`,
  })


  return (
    <>
      <Container bottom={16} centered>
        <div style={{ fontSize: "12px" }}>Updated {timeSince(cat5Data.updateTimestamp)} ago</div>
      </Container>
      <Container width={400} centered>
        <Select
          value={selectedMatchup}
          onChange={handleMatchupChange}
          style={{ marginBottom: 16, width: '100%' }}
        >
          {cat5Data.matchups.map((m, index) => (
            <Select.Option key={index} value={index}>
              {`${formatManager(teams[m.awayTeam])} \u21D4 ${formatManager(teams[m.homeTeam])}`}
            </Select.Option>
          ))}
        </Select>
        <Table
          columns={catTableColumns}
          dataSource={catTableDataSource}
          pagination={false}
          size="small"
          rowClassName={(record) => record.key === 'OVR' ? 'highlight-row' : ''}
        />
        <p className="forecast-explanation">
          Win more categories to win the matchup. Equal category wins are a tie.
        </p>
        <Container size={20}>
          <Radio.Group
            value={selectedRadio}
            onChange={handleRadioChange}
            block
          >
            <Radio.Button value="away">Away Best</Radio.Button>
            <Radio.Button value="default">Default</Radio.Button>
            <Radio.Button value="home">Home Best</Radio.Button>
          </Radio.Group>
        </Container>
      </Container >

      <Container width={400}>
        <section className="lineup-guide" aria-label="Start and sit guidance">
          <h3>Start / sit guide</h3>
          <Radio.Group
            aria-label="Team for start and sit guidance"
            value={selectedPlayerValue}
            onChange={e => { setSelectedPlayerValue(e.target.value); setDecisionFilter('All'); }}
            className="guidance-team-picker"
          >
            <Radio.Button value="awayPlayerValue">{formatManager(teams[matchup.awayTeam])}</Radio.Button>
            <Radio.Button value="homePlayerValue">{formatManager(teams[matchup.homeTeam])}</Radio.Button>
          </Radio.Group>
          {hasGuidance ? <>
            <div className="lineup-summary">
              <strong>{lineup.recommended} recommended starts · {lineup.unused} unused slots</strong>
              <p>{lineup.remaining} starts left under the cap · {lineup.available} eligible player games.</p>
              {forcedUnused > 0 && <p>{forcedUnused} slots cannot be filled with currently eligible games.</p>}
              {strategicUnused > 0 && <p>Leave {strategicUnused} more {strategicUnused === 1 ? 'slot' : 'slots'} unused to protect shooting percentages or turnovers.
                {typeof fullWin === 'number' && ` Estimated advantage over filling available slots: ${formatImpact(ownWin - fullWin)}.`}
              </p>}
              {lineup.remaining === 0 && <p>The game cap is reached. No remaining starts count toward this forecast.</p>}
              <details>
                <summary>Compare how many starts to use</summary>
                <p className="forecast-explanation">Best estimate found at each start count. Empty means no stats added. Search is approximate; daily slot and position constraints are not modeled.</p>
                <div className="start-counts">
                  {lineup.winByStarts.map(row => <div key={row.starts} className={row.starts === lineup.recommended ? 'chosen-count' : ''}>
                    <span>{row.starts} starts / {lineup.remaining - row.starts} unused</span>
                    <strong>{formatP(row.win)} win</strong>
                  </div>)}
                </div>
              </details>
            </div>
            <p className="forecast-explanation">Matchup-specific suggestions against the opponent's default lineup. Return-date games are conditional.</p>
            <details className="guidance-method">
              <summary>How decisions & impact work</summary>
              <p className="forecast-explanation">Impact is the average change in matchup win chance per eligible game, in percentage points (pp), against the best single-start alternative. For a selected game, compare removing or replacing it; for a bench game, compare adding it or replacing a selected game. Impacts are not additive.</p>
              <p className="forecast-explanation">Start / Sit means every eligible game favors that choice by more than 0.2 pp. Consider covers close or mixed decisions. These are model suggestions, not guarantees. Return-date games assume the player returns as estimated; daily slot and position constraints are not modeled.</p>
            </details>
            <Select
              aria-label="Filter player decisions"
              value={decisionFilter}
              onChange={setDecisionFilter}
              className="decision-filter"
              options={['All', 'Start', 'Consider', 'Sit', 'Unavailable', 'No games', 'Cap reached']
                .filter(decision => decision === 'All' || playerValue.some(value => value.decision === decision))
                .map(decision => ({ value: decision, label: `${decision === 'All' ? 'All players' : decision} (${decision === 'All' ? playerValue.length : playerValue.filter(value => value.decision === decision).length})` }))}
            />
          </> : <p className="forecast-explanation">Refresh forecasts to see the new start / sit guidance. The previous relative player scores are hidden until then.</p>}
          {hasGuidance && playerValue.filter(value => decisionFilter === 'All' || value.decision === decisionFilter).map(value => {
            const player = players[value.player];
            const conditional = player.injured && player.estimatedReturn;
            return <article className="player-card" key={value.player}>
              <div className="player-card-heading">
                <div>{formatPlayer(player)} <span className="player-pro-team">{player.proTeam}</span></div>
                <span className={`decision decision-${value.decision.toLowerCase().replaceAll(' ', '-')}`}>{value.decision}</span>
              </div>
              <div className="player-metrics">
                <span><strong>{value.recommended}/{value.eligible}</strong> starts recommended</span>
                <span>{value.eligible > 0 && lineup.remaining > 0 ? <><strong>{formatImpact(value.value)}</strong> / game</> : '—'}</span>
              </div>
              <p className="player-availability">{value.scheduled} scheduled · {value.eligible} eligible · {value.eligible - value.recommended} bench
                {value.scheduled > value.eligible && ` · ${value.scheduled - value.eligible} excluded`}
              </p>
              {(player.injured || player.injuryStatus === 'SUSPENSION') && <p className="injury-note">
                {player.injuryStatus || 'Injured'}{conditional ? ` · Estimated return ${player.estimatedReturn}; later starts conditional.` : ' · No usable return estimate; excluded games may change.'}
                {player.injuryNote && ` ${player.injuryNote}`}
              </p>}
              {value.starts.length > 0 && <details>
                <summary>Game decisions & impact</summary>
                <ul className="game-decisions">{value.starts.map((start, index) => <li key={`${start.date}-${index}`}>
                  <span>{gameDate(start.date)}</span>
                  <span>{start.selected ? 'Start' : 'Bench'} · {lineup.remaining > 0 ? formatImpact(start.impact) : 'cap reached'}</span>
                </li>)}</ul>
              </details>}
            </article>;
          })}
        </section>
      </Container>
    </>
  )
}

export default Forecast
