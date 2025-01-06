import PropTypes from 'prop-types';
import styled from "styled-components";

const Span = styled.span.attrs(({
  size = 4, left, right,
}) => ({
  size,
  left: left !== undefined ? left : size,
  right: right !== undefined ? right : size,
}))`
  padding-left: ${props => props.left}px;
  padding-right: ${props => props.right}px;
`

Span.propTypes = {
  size: PropTypes.number,
  left: PropTypes.number,
  right: PropTypes.number,
}

export default Span
