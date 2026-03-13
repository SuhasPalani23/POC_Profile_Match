const palette = {
  colors: {
    background: {
      primary: '#000000',
      secondary: '#0a0a0a',
      tertiary: '#111111',
    },
    primary: {
      cyan: '#c9a84c',
      blue: '#c9a84c',
      gradient: 'linear-gradient(135deg, #c9a84c 0%, #f0ede8 100%)',
    },
    text: {
      primary: '#f0ede8',
      secondary: '#8f8676',
      tertiary: '#555555',
    },
    status: {
      success: '#c9a84c',
      error: '#d86b6b',
      warning: '#c9a84c',
      info: '#f0ede8',
    },
    border: {
      primary: '#1a1a1a',
      secondary: '#2a2a2a',
      accent: '#c9a84c',
    },
  },

  typography: {
    fontFamily: {
      primary: "'DM Mono', monospace",
      mono: "'IBM Plex Mono', monospace",
      display: "'Cormorant Garamond', serif",
    },
    fontSize: {
      xs: '0.6875rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.375rem',
      '2xl': '1.75rem',
      '3xl': '2.375rem',
      '4xl': '3.125rem',
      '5xl': '4rem',
      '6xl': '5.5rem',
    },
    fontWeight: {
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
      extrabold: 800,
      black: 900,
    },
    lineHeight: {
      tight: 1.2,
      normal: 1.5,
      relaxed: 1.75,
    },
  },

  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    '2xl': '3rem',
    '3xl': '7.5rem',
  },

  borderRadius: {
    none: '0',
    sm: '0.25rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
    full: '9999px',
  },

  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
    md: '0 6px 20px -4px rgba(0, 0, 0, 0.35)',
    lg: '0 16px 34px -8px rgba(0, 0, 0, 0.5)',
    xl: '0 30px 60px -16px rgba(0, 0, 0, 0.7)',
    glow: '0 0 28px rgba(201, 168, 76, 0.15)',
    glowHover: '0 0 40px rgba(201, 168, 76, 0.22)',
  },

  transitions: {
    fast: '250ms',
    normal: '320ms',
    slow: '380ms',
  },

  zIndex: {
    dropdown: 1000,
    sticky: 1020,
    modal: 1030,
    popover: 1040,
    tooltip: 1050,
  },
};

export default palette;
