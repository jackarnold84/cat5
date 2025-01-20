import { Radio, Select, Table } from "antd";
import * as React from "react";
import '../styles/forecast.css';
import { timeSince } from "../utils/display";
import Container from "./common/Container";

const formatP = (p) => {
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

const formatV = (v) => (v * 100).toFixed(0);

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
  const teams = cat5Data.teams;
  const players = cat5Data.players

  const handleMatchupChange = (value) => {
    setSelectedMatchup(value);
    setSelectedRadio('default');
    setSelectedForecast('default');
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
    away: 1 - winP,
  }))
  catTableDataSource.push({
    key: 'OVR',
    cat: 'OVR',
    home: forecast.win,
    away: 1 - forecast.win,
  })
  catTableDataSource.push({
    key: 'GP',
    cat: 'GP',
    home: `${matchup.homeGP}/${cat5Data.maxGP}`,
    away: `${matchup.awayGP}/${cat5Data.maxGP}`,
  })

  // player table setup
  const playerTableColumns = [
    {
      dataIndex: 'player',
      key: 'player',
      align: 'left',
      width: '80%',
      render: (_, record) => (
        <>{formatPlayer(record.player)}</>
      ),
    },
    {
      dataIndex: 'value',
      key: 'value',
      align: 'right',
      width: '20%',
      render: (_, record) => (
        <>{formatV(record.value)}</>
      ),
    },
  ];
  const playerTableDataSource = playerValue.map((player) => ({
    key: player.player,
    player: players[player.player],
    value: player.value,
  }));

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

      <Container width={300} centered>
        <Table
          columns={playerTableColumns}
          dataSource={playerTableDataSource}
          pagination={false}
          size="small"
          showHeader={false}
          title={() => (
            <h4>
              {selectedPlayerValue === 'homePlayerValue' ? 'Home' : 'Away'}
              {` Best Starts`}
            </h4>
          )}
        />
      </Container>
    </>
  )
}

export default Forecast
