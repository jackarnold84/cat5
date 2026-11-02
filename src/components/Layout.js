import { MenuOutlined } from "@ant-design/icons"
import { Button, Drawer } from "antd"
import { Link } from "gatsby"
import * as React from "react"
import { BiLogoGithub } from "react-icons/bi"
import styled from "styled-components"
import '../styles/antd.less'
import '../styles/global.css'
import { palette } from "../utils/palette"
import Navigation from "./Navigation"
import Span from "./common/Span"

const Header = styled.header`
  padding: 8px 16px;
  background-color: ${palette.primary};
  color: white;
  text-align: center;
`

const HeaderContent = styled.div`
  margin: auto;
  max-width: 600px;
  position: relative;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
`

const BodyContainer = styled.main`
  margin: auto;
  max-width: 600px;
  min-height: calc(100svh - 120px);
  width: 100%;
  padding: 16px;
`

const Footer = styled.footer`
  padding: 8px 0;
  text-align: center;
  background-color: ${palette.primary};
`

const FooterContent = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
`

const MenuButtonHolder = styled.div`
  position: absolute;
  left: 0;
`

const Layout = ({ children }) => {
  const [openMenu, setOpenMenu] = React.useState(false);

  const showMenu = () => {
    setOpenMenu(true);
  };

  const closeMenu = () => {
    setOpenMenu(false);
  };

  return (
    <>
      <Header>
        <HeaderContent>
          <MenuButtonHolder>
            <Button type="primary" aria-label="Open navigation" aria-expanded={openMenu} icon={<MenuOutlined />} onClick={showMenu} />
          </MenuButtonHolder>
          <Link to="/" className="plain-link white-text">
            <h3>CAT5</h3>
          </Link>
        </HeaderContent>
      </Header>

      <BodyContainer>
        {children}
      </BodyContainer>

      <Footer>
        <FooterContent className="white-text subtext">
          <Span style={{ fontSize: "14px" }}>
            Created by Jack Arnold
          </Span>
          <Span>
            <Button
              type="text"
              size="small"
              style={{ color: "white", fontSize: "14px", textDecoration: "none" }}
              icon={<BiLogoGithub />}
              href="https://github.com/jackarnold84/cat5"
            >
              Github
            </Button>
          </Span>
        </FooterContent>
      </Footer>

      <Drawer title="CAT5" onClose={closeMenu} open={openMenu} placement="top" height="auto">
        <Navigation closeMenu={closeMenu} />
      </Drawer >
    </>
  )
}

export default Layout
