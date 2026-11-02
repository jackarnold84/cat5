import * as React from 'react';

// The keyed child resets a failed image immediately when its source changes.
const ImageWithFallback = ({ src, name, lazy }) => {
  const [failed, setFailed] = React.useState(false);
  const initials = (name || '?').trim().split(/\s+/).slice(0, 2).map(word => word[0]).join('');
  return <span className="identity-image" aria-hidden="true">
    {src && !failed ? <img
      src={src}
      alt=""
      width={48}
      height={48}
      loading={lazy ? 'lazy' : 'eager'}
      decoding="async"
      onError={() => setFailed(true)}
    /> : <span>{initials}</span>}
  </span>;
};

const IdentityImage = props => <ImageWithFallback key={props.src || 'missing'} {...props} />;

export default IdentityImage;
