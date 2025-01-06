import { Avatar, List, Skeleton } from "antd"
import React from "react"
import Layout from "../components/Layout"
import Container from "../components/common/Container"

const ApiPage = () => {

  const [isReady, setIsReady] = React.useState(false)
  const [isError, setIsError] = React.useState(false)
  const [mlbTeamData, setMlbTeamData] = React.useState([{}, {}, {}])
  React.useEffect(() => {
    const baseUrl = 'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams';
    const queryParams = new URLSearchParams({ 'test': 'abc' });
    const url = `${baseUrl}?${queryParams}`
    fetch(url,
      {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
        },
      },
    )
      .then(response => response.json())
      .then(result => {
        const teams = result.sports[0].leagues[0].teams
        const newMlbTeamData = teams.map(x => ({
          name: x.team.displayName,
          abbreviation: x.team.abbreviation,
          color: x.team.color,
        }))

        // display after 2 seconds
        setTimeout(() => {
          setMlbTeamData(newMlbTeamData)
          setIsReady(true)
        }, 2000)
      })
      .catch(error => {
        console.warn(error)
        setIsError(true)
      })
  }, []) // must include empty array

  return (
    <Layout>
      <Container size={16} centered >
        <h2>Example API Call</h2>
      </Container>

      <Container size={16} centered >
        <h4>MLB Teams</h4>
      </Container>

      {isError ? (
        <Container centered >
          <div>There was an error calling the API</div>
        </Container>
      ) : (
        <Container>
          <List
            itemLayout="horizontal"
            size="small"
            dataSource={mlbTeamData}
            renderItem={item => (
              <List.Item>
                <Skeleton avatar title={false} loading={!isReady} active>
                  <List.Item.Meta
                    avatar={
                      <Avatar style={{ backgroundColor: `#${item.color}` }}>
                        {item.abbreviation}
                      </Avatar>
                    }
                    title={item.name}
                    href={`https://www.mlb.com/${item.abbreviation}`}
                  />
                </Skeleton>
              </List.Item>
            )}
          />
        </Container>
      )
      }

    </Layout >
  )
}

export default ApiPage

export const Head = () => <title>API Page</title>
