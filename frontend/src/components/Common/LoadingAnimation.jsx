import React, { useEffect, useState } from 'react';
import palette from '../../palette';

const LoadingAnimation = ({ message = 'Processing...', duration = 10000 }) => {
  const [visibleText, setVisibleText] = useState('');
  const text = 'SCANNING THE TALENT POOL';

  useEffect(() => {
    let index = 0;
    const interval = setInterval(() => {
      index += 1;
      setVisibleText(text.slice(0, index));
      if (index >= text.length) clearInterval(interval);
    }, 55);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="cinematic-loader" style={{ minHeight: '500px' }}>
      <div style={{
        position: 'relative',
        zIndex: 2,
        display: 'grid',
        justifyItems: 'center',
        gap: palette.spacing.md,
        textAlign: 'center',
      }}>
        <div className="pulse-ring" />
        <p className="mono-label">{visibleText}</p>
        <p style={{
          color: palette.colors.text.secondary,
          maxWidth: '420px',
          fontSize: palette.typography.fontSize.sm,
          lineHeight: palette.typography.lineHeight.relaxed,
        }}>
          {message}
        </p>
      </div>
    </div>
  );
};

export default LoadingAnimation;
