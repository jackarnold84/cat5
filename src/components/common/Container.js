import PropTypes from 'prop-types';
import styled from "styled-components";

const Container = styled('div').withConfig({
  shouldForwardProp: (prop) => !['centered', 'flex', 'top', 'bottom', 'size', 'width'].includes(prop),
}).attrs(({
  size = 8, top, bottom, width, centered = false, flex = false,
}) => ({
  size,
  top: top !== undefined ? top : size,
  bottom: bottom !== undefined ? bottom : size,
  width,
  centered,
  flex,
}))`
  margin: auto;
  padding-top: ${props => props.top}px;
  padding-bottom: ${props => props.bottom}px;
  ${({ width }) => width && `
    max-width: ${width}px;
  `}
  ${({ centered }) => centered && `
    text-align: center;
    justify-content: center;
  `}
  ${({ flex }) => flex && `
    display: flex;
  `}
`;


Container.propTypes = {
  size: PropTypes.number,
  top: PropTypes.number,
  bottom: PropTypes.number,
  width: PropTypes.number,
  centered: PropTypes.bool,
  flex: PropTypes.bool,
}

export default Container
