import { Radio, Table } from "antd";
import * as React from "react";
import '../styles/forecast.css';
import { timeSince } from "../utils/display";
import Container from "./common/Container";
import IdentityImage from "./common/IdentityImage";

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
  const opacity = Math.max(0, Math.min(1, p)) * 0.8;
  return `rgba(200, 15, 45, ${opacity})`;
}

const formatImpact = (v) => {
  const points = Number((v * 100).toFixed(2));
  return `${points > 0 ? '+' : ''}${points.toFixed(2)} pp`;
};
const gameDate = (value) => new Date(value).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });

const formatManager = (team) => {
  const parts = (team.manager || team.name || 'Team').trim().split(/\s+/);
  return parts.length > 1 ? `${parts[0]} ${parts[parts.length - 1].charAt(0)}` : parts[0];
};

const Forecast = ({ cat5Data }) => {
  // selectors
  const [selectedMatchup, setSelectedMatchup] = React.useState(0);
  const [selectedRadio, setSelectedRadio] = React.useState('default');
  const [selectedForecast, setSelectedForecast] = React.useState('default');
  const [selectedPlayerValue, setSelectedPlayerValue] = React.useState('homePlayerValue');
  const teams = cat5Data.teams;
  const players = cat5Data.players

  const handleMatchupChange = (value) => {
    setSelectedMatchup(value);
    setSelectedRadio('default');
    setSelectedForecast('default');
    setSelectedPlayerValue('homePlayerValue');
  };

  const handleRadioChange = (e) => {
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
          color: record.key !== 'GP' ? '#000' : undefined,
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
          <div>{record.cat === 'OVR' ? 'Overall' : record.cat}</div>
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
          color: record.key !== 'GP' ? '#000' : undefined,
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
        <div className="forecast-explanation">Updated {timeSince(cat5Data.updateTimestamp)} ago</div>
      </Container>
      <Container width={568} centered>
        <select
          aria-label="Select matchup"
          value={selectedMatchup}
          onChange={event => handleMatchupChange(Number(event.target.value))}
          className="forecast-select matchup-select"
        >
          {cat5Data.matchups.map((m, index) => (
            <option key={index} value={index}>
              {`${formatManager(teams[m.awayTeam])} \u21D4 ${formatManager(teams[m.homeTeam])}`}
            </option>
          ))}
        </select>
        <div className="matchup-heading">
          {[matchup.awayTeam, matchup.homeTeam].map((id, index) => <React.Fragment key={id}>
            {index === 1 && <span className="matchup-versus">vs</span>}
            <div className="matchup-team">
              <IdentityImage src={teams[id].logoUrl} name={teams[id].name} />
              <strong>{teams[id].name}</strong>
              <span>{formatManager(teams[id])} · {index === 0 ? 'Away' : 'Home'}</span>
            </div>
          </React.Fragment>)}
        </div>
        <Table
          className="forecast-table"
          tableLayout="fixed"
          columns={catTableColumns}
          dataSource={catTableDataSource}
          pagination={false}
          size="small"
          rowClassName={(record) => record.key === 'OVR' ? 'highlight-row' : ''}
        />
        <Container size={20}>
          <Radio.Group
            value={selectedRadio}
            onChange={handleRadioChange}
            className="forecast-mode"
            aria-label="Forecast lineup"
          >
            <Radio.Button value="away">Away Best</Radio.Button>
            <Radio.Button value="default">Default</Radio.Button>
            <Radio.Button value="home">Home Best</Radio.Button>
          </Radio.Group>
        </Container>
      </Container >

      <Container width={568}>
        <section className="lineup-guide" aria-label="Start and sit guidance">
          <h3>Start / sit guide</h3>
          <Radio.Group
            aria-label="Team for start and sit guidance"
            value={selectedPlayerValue}
            onChange={e => setSelectedPlayerValue(e.target.value)}
            className="guidance-team-picker"
          >
            <Radio.Button value="awayPlayerValue">{formatManager(teams[matchup.awayTeam])}</Radio.Button>
            <Radio.Button value="homePlayerValue">{formatManager(teams[matchup.homeTeam])}</Radio.Button>
          </Radio.Group>
          {hasGuidance ? <>
            <div className="lineup-summary">
              <strong>{lineup.recommended} recommended starts · {lineup.unused} unused slots</strong>
              <p>{lineup.remaining} starts left · {lineup.available} eligible games.</p>
              {forcedUnused > 0 && <p>{forcedUnused} slots unfillable.</p>}
              {strategicUnused > 0 && <p>Leave {strategicUnused} slots unused.</p>}
              {lineup.remaining === 0 && <p>Game cap reached.</p>}
              <details>
                <summary>Starts comparison</summary>
                <div className="start-counts">
                  {lineup.winByStarts.map(row => <div key={row.starts} className={row.starts === lineup.recommended ? 'chosen-count' : ''}>
                    <span>{row.starts} starts / {lineup.remaining - row.starts} unused</span>
                    <strong>{formatP(row.win)} win</strong>
                  </div>)}
                </div>
              </details>
            </div>
          </> : <p className="forecast-explanation">Refresh forecasts for start / sit guidance.</p>}
          {hasGuidance && playerValue.map(value => {
            const player = players[value.player];
            const conditional = player.injured && player.estimatedReturn;
            return <article className="player-card" key={value.player}>
              <div className="player-card-heading">
                <div className="player-identity">
                  <IdentityImage
                    src={/^[1-9]\d*$/.test(value.player) ? `https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/${value.player}.png&w=96` : null}
                    name={player.name}
                    lazy
                  />
                  <div><strong>{player.name}</strong><div className="player-pro-team">{player.pos} · {player.proTeam}</div></div>
                </div>
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
                {player.injuryStatus || 'Injured'}{conditional ? ` · Est. return ${player.estimatedReturn} (conditional)` : ''}
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
