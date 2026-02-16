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
          background: palette.colors.primary.gradient,
          color: palette.colors.background.primary,
          border: 'none',
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
          color: palette.colors.primary.cyan,
          border: `1px solid ${palette.colors.primary.cyan}`,
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
          fontSize: palette.typography.fontSize.sm,
        };
      case 'md':
        return {
          padding: `${palette.spacing.md} ${palette.spacing.lg}`,
          fontSize: palette.typography.fontSize.base,
        };
      case 'lg':
        return {
          padding: `${palette.spacing.lg} ${palette.spacing.xl}`,
          fontSize: palette.typography.fontSize.lg,
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
        fontWeight: palette.typography.fontWeight.semibold,
        borderRadius: palette.borderRadius.md,
        cursor: disabled || loading ? 'not-allowed' : 'pointer',
        opacity: disabled || loading ? 0.6 : 1,
        transition: `all ${palette.transitions.normal}`,
        fontFamily: palette.typography.fontFamily.primary,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: palette.spacing.sm,
        ...style,
      }}
      onMouseEnter={(e) => {
        if (!disabled && !loading && variant === 'primary') {
          e.target.style.opacity = '0.9';
          e.target.style.boxShadow = palette.shadows.glow;
        }
      }}
      onMouseLeave={(e) => {
        if (!disabled && !loading) {
          e.target.style.opacity = '1';
          e.target.style.boxShadow = 'none';
        }
      }}
    >
      {loading && (
        <div style={{
          width: '16px',
          height: '16px',
          border: '2px solid transparent',
          borderTop: `2px solid ${variant === 'primary' ? palette.colors.background.primary : palette.colors.primary.cyan}`,
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
        }} />
      )}
      {children}
    </button>
  );
};

export default Button;