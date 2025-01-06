import React from "react"

import Layout from "../components/Layout"
import Container from "../components/common/Container"
import Plot from "../components/common/Plot"
import { palette } from "../utils/palette"


const PlotPage = () => {
  return (
    <Layout>
      <Container size={16} centered >
        <h2>Plots</h2>
      </Container>

      <Container size={16} centered >
        <h3>Sales Data</h3>
      </Container>

      <Container >
        <Plot
          height={300}
          data={[
            {
              name: 'Sales',
              x: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
              y: [10, 15, 13, 17, 18, 20, 19, 15, 16, 14],
              type: 'scatter',
              hovertemplate: '<b>Week %{x}</b><br>%{y} sold',
              marker: { color: palette.purple },
            }
          ]}
          layout={{
            xaxis: { title: 'Week', fixedrange: true },
            yaxis: { title: 'Products Sold', fixedrange: true },
          }}
        />
      </Container>
    </Layout>
  )
}

export default PlotPage

export const Head = () => <title>Plot Page</title>
