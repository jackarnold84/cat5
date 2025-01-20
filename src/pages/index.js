import { Button, List } from "antd"
import { Link } from "gatsby"
import * as React from "react"
import { BiBasketball } from "react-icons/bi"
import styled from "styled-components"
import Layout from "../components/Layout"
import Container from "../components/common/Container"
import logo from "../images/logo.png"

const NavLink = styled(Link)`
  margin: auto;
  width: 100%;
`

const IndexPage = () => {
  const links = [
    { to: "/forecast?tag=demon", icon: <BiBasketball />, text: "Demon League" },
  ]

  return (
    <Layout>
      <Container centered>
        <img
          src={logo}
          alt="CAT5 Logo"
          width={200}
          height={200}
        />
      </Container>
      <Container size={16} centered>
        <h4>Who will win category number 5?</h4>
      </Container>

      <Container size={16} width={400}>
        <Container centered>
          <h3>Leagues</h3>
        </Container>
        <List
          size="small"
          dataSource={links}
          renderItem={item => (
            <List.Item>
              <NavLink to={item.to}>
                <Button type="default" icon={item.icon} size="large" block >
                  {item.text}
                </Button>
              </NavLink>
            </List.Item>
          )}
        />
      </Container>
    </Layout>
  )
}

export default IndexPage

export const Head = () => <title>CAT5 - Home</title>
