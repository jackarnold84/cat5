import { Button, Skeleton } from "antd"
import { Link } from "gatsby"
import React from "react"
import Container from "../components/common/Container"
import Forecast from "../components/Forecast"
import Layout from "../components/Layout"
import config from '../config.json'

const API_ENDPOINT = 'https://1jk32bv8k9.execute-api.us-east-2.amazonaws.com/Prod/cat5/data/'

const ApiPage = ({ location }) => {
  // get query params
  const urlParams = new Proxy(new URLSearchParams(location.search), {
    get: (searchParams, prop) => searchParams.get(prop),
  });
  const tag = urlParams.tag

  // call API
  const [isReady, setIsReady] = React.useState(false)
  const [isError, setIsError] = React.useState(false)
  const [cat5Data, setCat5Data] = React.useState([{}])
  React.useEffect(() => {
    const url = `${API_ENDPOINT}${tag}`
    fetch(url,
      {
        method: 'GET',
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
        console.warn(error)
        setIsError(true)
      })
  }, [tag])

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
          <div>There was an error calling the API</div>
        </Container>
      ) : !isReady ? (
        <Container>
          <Skeleton active />
        </Container>
      ) : (
        <Forecast cat5Data={cat5Data} />
      )}

    </Layout >
  )
}

export default ApiPage

export const Head = () => <title>CAT5 - Forecast</title>
