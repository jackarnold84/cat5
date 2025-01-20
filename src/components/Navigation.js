import { HomeOutlined } from "@ant-design/icons"
import { Button, List } from "antd"
import { Link } from "gatsby"
import * as React from "react"
import styled from "styled-components"

const NavLink = styled(Link)`
  margin: auto;
  width: 100%;
`

const Navigation = ({ closeMenu }) => {
  const links = [
    { to: "/", icon: <HomeOutlined />, text: "Home" },
  ]

  return (
    <>
      <List
        size="small"
        dataSource={links}
        renderItem={item => (
          <List.Item>
            <NavLink to={item.to}>
              <Button type="text" icon={item.icon} size="large" block onClick={closeMenu} >
                {item.text}
              </Button>
            </NavLink>
          </List.Item>
        )}
      />
    </>
  )
}

export default Navigation
