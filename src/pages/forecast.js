import { Button, Skeleton } from "antd"
import { Link } from "gatsby"
import React from "react"
import Container from "../components/common/Container"
import Forecast from "../components/Forecast"
import Layout from "../components/Layout"
import config from '../config.json'

const API_ENDPOINT = 'https://1jk32bv8k9.execute-api.us-east-2.amazonaws.com/Prod/cat5/data/'

const ApiPage = ({ location }) => {
  // Static HTML and the first browser render must agree before reading the query.
  const [tag, setTag] = React.useState(null)
  React.useEffect(() => {
    setTag(new URLSearchParams(location.search).get('tag') || '')
  }, [location.search])

  // call API
  const [isReady, setIsReady] = React.useState(false)
  const [isError, setIsError] = React.useState(false)
  const [cat5Data, setCat5Data] = React.useState(null)
  React.useEffect(() => {
    if (!config.leagues[tag]) return
    const controller = new AbortController()
    setIsReady(false)
    setIsError(false)
    const url = `${API_ENDPOINT}${tag}`
    fetch(url,
      {
        method: 'GET',
        signal: controller.signal,
        headers: {
          'Accept': 'application/json',
        },
      },
    )
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(result => {
        setCat5Data(result)
        setIsReady(true)
      })
      .catch(error => {
        if (error.name === 'AbortError') return
        console.warn(error)
        setIsError(true)
      })
    return () => controller.abort()
  }, [tag])

  if (tag === null) {
    return (
      <Layout>
        <Container>
          <div role="status" aria-label="Loading forecasts"><Skeleton active /></div>
        </Container>
      </Layout>
    )
  }

  // tag not found
  if (!config.leagues[tag]) {
    return (
      <Layout>
        <Container centered>
          <h2>League Not Found</h2>
        </Container>
        <Container centered >
          <Link to="/">
            <Button type="primary">Home</Button>
          </Link>
        </Container>
      </Layout>
    )
  }

  // render
  return (
    <Layout>
      <Container top={16} bottom={0} centered >
        <h2>{config.leagues[tag].name}</h2>
        <Container>
          <h4>Matchup Forecast</h4>
        </Container>
      </Container>

      {isError ? (
        <Container centered >
          <div className="page-state" role="alert">Unable to load forecasts. Please try refreshing the page.</div>
        </Container>
      ) : !isReady ? (
        <Container>
          <div role="status" aria-label="Loading forecasts"><Skeleton active /></div>
        </Container>
      ) : cat5Data.year !== config.leagues[tag].year ? (
        <Container centered>
          <div className="page-state">The {config.leagues[tag].year - 1}–{String(config.leagues[tag].year).slice(-2)} forecast is not available yet.</div>
        </Container>
      ) : cat5Data.matchups.length === 0 ? (
        <Container centered><div className="page-state">No active matchups are available.</div></Container>
      ) : (
        <Forecast cat5Data={cat5Data} />
      )}

    </Layout >
  )
}

export default ApiPage

export const Head = () => <title>CAT5 - Forecast</title>
