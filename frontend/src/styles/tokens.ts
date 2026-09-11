// src/styles/tokens.ts
// Design System Tokens - استانداردسازی رنگ، فضا، و تایپوگرافی

export const designTokens = {
  colors: {
    // Primary Palette - Leaf (Green)
    leaf: {
      50: '#f0fdf4',
      100: '#dcfce7',
      200: '#b5f0cd',
      300: '#7ee2a8',
      400: '#4cd08a',
      500: '#2fb36b',
      600: '#1f9155',
      700: '#177246',
      800: '#155f3c',
      900: '#145033',
    },
    // Accent Palette - Sand (Warm)
    sand: {
      50: '#fffbeb',
      100: '#fef3c7',
      200: '#f7e3bd',
      300: '#f2d49b',
      400: '#e6b96b',
      500: '#d49b3f',
      600: '#b88125',
      700: '#9c6a1a',
    },
    // Accent Palette - Aqua (Cool)
    aqua: {
      50: '#f0fdfa',
      100: '#ccfbf1',
      200: '#c5ecf4',
      300: '#7fd8e8',
      400: '#45bcd4',
      500: '#2a9bb5',
      600: '#1d7a8c',
      700: '#1a5f6d',
    },
    // Neutral Palette - Night (Dark)
    night: {
      50: '#f5f7f5',
      100: '#e6f0ea',
      200: '#c7dfd3',
      300: '#9bbdaf',
      400: '#6e8c89',
      500: '#4a7068',
      600: '#3a5a52',
      700: '#2e4a42',
      800: '#1a3a33',
      900: '#071811',
      950: '#04100b',
    },
  },
  
  spacing: {
    xs: '0.25rem',   // 4px
    sm: '0.5rem',    // 8px
    md: '0.75rem',   // 12px
    lg: '1rem',      // 16px
    xl: '1.25rem',   // 20px
    '2xl': '1.5rem', // 24px
    '3xl': '1.75rem',// 28px
    '4xl': '2rem',   // 32px
    '5xl': '2.5rem', // 40px
    '6xl': '3rem',   // 48px
    '7xl': '3.5rem', // 56px
    '8xl': '4rem',   // 64px
  },
  
  fontSize: {
    xs: { size: '0.75rem', lineHeight: '1rem' },
    sm: { size: '0.875rem', lineHeight: '1.25rem' },
    base: { size: '1rem', lineHeight: '1.5rem' },
    lg: { size: '1.125rem', lineHeight: '1.75rem' },
    xl: { size: '1.25rem', lineHeight: '1.75rem' },
    '2xl': { size: '1.5rem', lineHeight: '2rem' },
    '3xl': { size: '1.75rem', lineHeight: '2.25rem' },
    '4xl': { size: '2rem', lineHeight: '2.5rem' },
    '5xl': { size: '2.25rem', lineHeight: '2.5rem' },
    '6xl': { size: '2.5rem', lineHeight: '2.5rem' },
  },
  
  fontWeight: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
    extrabold: '800',
  },
  
  borderRadius: {
    none: '0',
    sm: '0.125rem',  // 2px
    md: '0.375rem',  // 6px
    lg: '0.5rem',    // 8px
    xl: '0.75rem',   // 12px
    '2xl': '1rem',   // 16px
    '3xl': '1.5rem', // 24px
    full: '9999px',
  },
  
  boxShadow: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    DEFAULT: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  },
  
  animation: {
    duration: {
      fast: '0.15s',
      normal: '0.3s',
      slow: '0.6s',
      slower: '0.9s',
    },
    easing: {
      standard: 'cubic-bezier(0.4, 0, 0.2, 1)',
      emphasized: 'cubic-bezier(0.2, 0, 0, 1)',
      standardAccelerate: 'cubic-bezier(0.3, 0, 0.8, 0.15)',
      standardDecelerate: 'cubic-bezier(0, 0, 0, 1)',
    },
  },
  
  zIndex: {
    hide: 10,
    auto: 'auto',
    base: 0,
    dropdown: 1000,
    sticky: 1100,
    overlay: 1200,
    modal: 1300,
    popover: 1400,
    tooltip: 1500,
  },
};

// Theme-specific tokens
export const lightTheme = {
  background: designTokens.colors.night[50],
  surface: designTokens.colors.night[100],
  border: designTokens.colors.night[300],
  text: designTokens.colors.night[900],
  textMuted: designTokens.colors.night[500],
};

export const darkTheme = {
  background: designTokens.colors.night[950],
  surface: designTokens.colors.night[900],
  border: designTokens.colors.night[700],
  text: designTokens.colors.night[100],
  textMuted: designTokens.colors.night[400],
};

// Utility functions
export const getColor = (palette: string, shade: string): string => {
  const colorPalettes = designTokens.colors;
  const targetPalette = colorPalettes[palette as keyof typeof colorPalettes];
  if (targetPalette) {
    return (targetPalette as Record<string, string>)[shade] || '';
  }
  return '';
};

export const getSpacing = (size: string): string => {
  return designTokens.spacing[size as keyof typeof designTokens.spacing] || '0';
};

export const getFontSize = (size: string): { size: string; lineHeight: string } => {
  return designTokens.fontSize[size as keyof typeof designTokens.fontSize] || { size: '1rem', lineHeight: '1.5rem' };
};

export const getBorderRadius = (size: string): string => {
  return designTokens.borderRadius[size as keyof typeof designTokens.borderRadius] || '0';
};

export const getBoxShadow = (size: string): string => {
  return designTokens.boxShadow[size as keyof typeof designTokens.boxShadow] || 'none';
};

export const getZIndex = (level: string): number | string => {
  return designTokens.zIndex[level as keyof typeof designTokens.zIndex] || 0;
};

export default designTokens;