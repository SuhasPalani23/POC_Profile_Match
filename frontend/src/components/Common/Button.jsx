import React from 'react';
import palette from '../../palette';

const Button = ({
  children,
  onClick,
  type = 'button',
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  fullWidth = false,
  style = {},
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'primary':
        return {
          background: 'transparent',
          color: palette.colors.primary.cyan,
          border: `1px solid ${palette.colors.primary.cyan}`,
        };
      case 'secondary':
        return {
          background: 'transparent',
          color: palette.colors.text.primary,
          border: `1px solid ${palette.colors.border.primary}`,
        };
      case 'outline':
        return {
          background: 'transparent',
          color: palette.colors.text.secondary,
          border: `1px solid ${palette.colors.border.secondary}`,
        };
      default:
        return {};
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'sm':
        return {
          padding: `${palette.spacing.sm} ${palette.spacing.md}`,
          fontSize: palette.typography.fontSize.xs,
          letterSpacing: '0.14em',
        };
      case 'md':
        return {
          padding: `${palette.spacing.md} ${palette.spacing.lg}`,
          fontSize: palette.typography.fontSize.sm,
          letterSpacing: '0.16em',
        };
      case 'lg':
        return {
          padding: `${palette.spacing.lg} ${palette.spacing.xl}`,
          fontSize: palette.typography.fontSize.sm,
          letterSpacing: '0.18em',
        };
      default:
        return {};
    }
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      style={{
        ...getVariantStyles(),
        ...getSizeStyles(),
        width: fullWidth ? '100%' : 'auto',
        fontWeight: palette.typography.fontWeight.medium,
        borderRadius: palette.borderRadius.md,
        cursor: disabled || loading ? 'not-allowed' : 'pointer',
        opacity: disabled || loading ? 0.55 : 1,
        transition: `all ${palette.transitions.normal} cubic-bezier(0.16, 1, 0.3, 1)`,
        fontFamily: palette.typography.fontFamily.primary,
        textTransform: 'uppercase',
        position: 'relative',
        overflow: 'hidden',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: palette.spacing.sm,
        isolation: 'isolate',
        ...style,
      }}
      onMouseEnter={(e) => {
        if (!disabled && !loading) {
          e.currentTarget.style.boxShadow = palette.shadows.glow;
          e.currentTarget.style.color = '#000000';
          const wipe = e.currentTarget.querySelector('.button-wipe');
          if (wipe) wipe.style.transform = 'scaleX(1)';
        }
      }}
      onMouseLeave={(e) => {
        if (!disabled && !loading) {
          e.currentTarget.style.boxShadow = 'none';
          e.currentTarget.style.color =
            variant === 'primary' ? palette.colors.primary.cyan : variant === 'secondary' ? palette.colors.text.primary : palette.colors.text.secondary;
          const wipe = e.currentTarget.querySelector('.button-wipe');
          if (wipe) wipe.style.transform = 'scaleX(0)';
        }
      }}
      onMouseDown={(e) => {
        if (!disabled && !loading) e.currentTarget.style.transform = 'scale(0.98)';
      }}
      onMouseUp={(e) => {
        if (!disabled && !loading) e.currentTarget.style.transform = 'scale(1)';
      }}
    >
      <span
        className="button-wipe"
        style={{
          position: 'absolute',
          inset: 0,
          backgroundColor: palette.colors.primary.cyan,
          transform: 'scaleX(0)',
          transformOrigin: 'left',
          transition: `transform ${palette.transitions.normal} cubic-bezier(0.16, 1, 0.3, 1)`,
          zIndex: -1,
        }}
      />
      {loading && (
        <div style={{
          width: '14px',
          height: '14px',
          border: `1px solid ${palette.colors.primary.cyan}`,
          borderRadius: '50%',
          animation: 'pulse-ring 1.6s cubic-bezier(0.16, 1, 0.3, 1) infinite',
        }} />
      )}
      {children}
    </button>
  );
};

export default Button;
