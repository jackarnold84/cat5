import { Button } from "antd"
import { Link } from "gatsby"
import * as React from "react"
import styled from "styled-components"
import Layout from "../components/Layout"
import Container from "../components/common/Container"

const PageHeading = styled.h2`
  text-align: center;
  padding-bottom: 16px;
`

const NotFoundPage = () => {
  return (
    <Layout>
      <Container size={16}>
        <PageHeading>Page Not Found</PageHeading>
        <Container centered>
          <Link to="/">
            <Button type="primary">Home</Button>
          </Link>
        </Container>
      </Container>
    </Layout>
  )
}

export default NotFoundPage

export const Head = () => <title>Not found</title>
