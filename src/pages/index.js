import { TruckOutlined } from "@ant-design/icons"
import { Button, Form, Input, Radio, Table } from "antd"
import * as React from "react"
import styled from "styled-components"
import Layout from "../components/Layout"
import Container from "../components/common/Container"
import Span from "../components/common/Span"

const SectionHeader = styled.h3`
  text-align: center;
  padding-top: 8px;
  padding-bottom: 16px;
`

const IndexPage = () => {
  const [tab, setTab] = React.useState('apple')

  return (
    <Layout>
      <Container size={16} centered>
        <h2>Gatsby Template</h2>
        <p>Starter template for Gatsby projects with various reusable components</p>
      </Container>


      <Container size={16} width={400}>
        <SectionHeader>Sign In Form</SectionHeader>
        <Form
          onFinish={(values) => { console.log(values) }}
          autoComplete="off"
          layout="vertical"
        >
          <Form.Item label="Username" name="username" rules={[{ required: true }]} >
            <Input />
          </Form.Item>
          <Form.Item label="Password" name="password" rules={[{ required: true }]} >
            <Input.Password />
          </Form.Item>
          <Container centered>
            <Form.Item>
              <Button type="primary" htmlType="submit">Submit</Button>
            </Form.Item>
          </Container>
        </Form>
      </Container>

      <Container size={16} width={500}>
        <SectionHeader>Statistics</SectionHeader>
        <Table
          columns={[
            { title: 'Brand', dataIndex: 'brand', key: 'brand' },
            { title: 'Model', dataIndex: 'model', key: 'model' },
            { title: 'Loft', dataIndex: 'loft', key: 'loft', sorter: (a, b) => a.loft - b.loft },
          ]}
          dataSource={[
            { key: 1, brand: 'Titleist', model: '775CB', loft: 37 },
            { key: 2, brand: 'Mizuno', model: 'JPX923 Hot Metal', loft: 33 },
            { key: 3, brand: 'Ping', model: 'G425', loft: 34.5 },
            { key: 4, brand: 'Taylormade', model: 'Stealth', loft: 32 },
          ]}
          size="small"
          pagination={false}
        />
      </Container>

      <Container size={16} width={500}>
        <SectionHeader>Tabs</SectionHeader>
        <Container centered>
          <Radio.Group
            options={[
              { label: 'Apple', value: 'apple' },
              { label: 'Pear', value: 'pear' },
              { label: 'Orange', value: 'orange' }
            ]}
            optionType="button"
            buttonStyle="solid"
            value={tab}
            onChange={({ target }) => { setTab(target.value) }}
          />
        </Container>

        <Container centered>
          <Span>
            <TruckOutlined />
          </Span>
          <Span>
            Truck full of {tab}s
          </Span>
        </Container>

      </Container>
    </Layout>
  )
}

export default IndexPage

export const Head = () => <title>Home Page</title>
