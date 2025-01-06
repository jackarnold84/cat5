import { LoadingOutlined } from '@ant-design/icons';
import React from "react";
import Loadable from "react-loadable";
import { plotlyConfig, plotlyLayout, plotlyProps } from '../../utils/plotly';

/*
  documentation:
  https://plotly.com/javascript/basic-charts/
*/

const Plot = ({ height, data, layout, config, ...props }) => {
  const LoadablePlot = Loadable({
    loader: () => import('react-plotly.js'),
    loading() {
      return (
        <div style={{ height, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <LoadingOutlined style={{ fontSize: '24px' }} />
        </div>
      );
    },
  });

  return (
    <div style={{ minHeight: height }}>
      <LoadablePlot
        data={data}
        layout={{
          height,
          ...plotlyLayout,
          ...layout,
        }}
        config={
          {
            ...plotlyConfig,
            ...config,
          }
        }
        {...plotlyProps}
        {...props}
      />
    </div>
  )
}

export default Plot
