import React, { useState, useEffect } from 'react';
import palette from '../../palette';

const LoadingAnimation = ({ message = "Processing...", duration = 10000 }) => {
  const [progress, setProgress] = useState(0);
  const [dots, setDots] = useState('');

  useEffect(() => {
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(progressInterval);
          return 100;
        }
        return prev + (100 / (duration / 100));
      });
    }, 100);

    const dotsInterval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? '' : prev + '.');
    }, 500);

    return () => {
      clearInterval(progressInterval);
      clearInterval(dotsInterval);
    };
  }, [duration]);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: palette.spacing['3xl'],
    }}>
      {/* Animated Circle */}
      <div style={{
        position: 'relative',
        width: '120px',
        height: '120px',
        marginBottom: palette.spacing.xl,
      }}>
        {/* Outer ring */}
        <div style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          border: `4px solid ${palette.colors.border.primary}`,
          borderRadius: '50%',
        }} />
        
        {/* Animated ring */}
        <div style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          border: '4px solid transparent',
          borderTop: `4px solid ${palette.colors.primary.cyan}`,
          borderRight: `4px solid ${palette.colors.primary.blue}`,
          borderRadius: '50%',
          animation: 'spin 2s linear infinite',
        }} />

        {/* Progress percentage */}
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          fontSize: palette.typography.fontSize['2xl'],
          fontWeight: palette.typography.fontWeight.bold,
          background: palette.colors.primary.gradient,
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}>
          {Math.round(progress)}%
        </div>
      </div>

      {/* Message */}
      <h3 style={{
        fontSize: palette.typography.fontSize.xl,
        fontWeight: palette.typography.fontWeight.semibold,
        color: palette.colors.text.primary,
        marginBottom: palette.spacing.sm,
      }}>
        {message}{dots}
      </h3>

      {/* Progress bar */}
      <div style={{
        width: '300px',
        height: '6px',
        backgroundColor: palette.colors.background.primary,
        borderRadius: palette.borderRadius.full,
        overflow: 'hidden',
        marginTop: palette.spacing.lg,
      }}>
        <div style={{
          width: `${progress}%`,
          height: '100%',
          background: palette.colors.primary.gradient,
          transition: 'width 0.3s ease',
          borderRadius: palette.borderRadius.full,
        }} />
      </div>

      <p style={{
        marginTop: palette.spacing.lg,
        color: palette.colors.text.secondary,
        fontSize: palette.typography.fontSize.sm,
        textAlign: 'center',
      }}>
        Our AI is analyzing your vision and finding the perfect team members...
      </p>
    </div>
  );
};

export default LoadingAnimation;