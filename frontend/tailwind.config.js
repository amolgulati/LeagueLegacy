/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      // Consistent color palette for the app
      colors: {
        // Brand colors
        brand: {
          gold: '#FFD700',
          orange: '#FFA500',
          trophy: '#B8860B',
        },
        // Platform colors
        sleeper: {
          DEFAULT: '#00B2E3',
          dark: '#0091B8',
        },
        yahoo: {
          DEFAULT: '#720E9E',
          dark: '#5A0B7E',
        },
      },
      // Custom animations
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out forwards',
        'slide-in-right': 'slideInFromRight 0.3s ease-out forwards',
        'slide-in-bottom': 'slideInFromBottom 0.4s ease-out forwards',
        'card-entrance': 'cardEntrance 0.4s ease-out forwards',
        'trophy-glow': 'trophyGlow 2s ease-in-out infinite',
        'pulse-scale': 'pulseScale 2s ease-in-out infinite',
        'count-up': 'countUp 0.5s ease-out forwards',
        'shimmer': 'shimmer 1.5s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0', transform: 'translateY(10px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        slideInFromRight: {
          from: { opacity: '0', transform: 'translateX(20px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
        slideInFromBottom: {
          from: { opacity: '0', transform: 'translateY(20px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        cardEntrance: {
          from: { opacity: '0', transform: 'scale(0.95) translateY(10px)' },
          to: { opacity: '1', transform: 'scale(1) translateY(0)' },
        },
        trophyGlow: {
          '0%, 100%': { filter: 'drop-shadow(0 0 10px rgba(255, 215, 0, 0.5))' },
          '50%': { filter: 'drop-shadow(0 0 20px rgba(255, 215, 0, 0.8))' },
        },
        pulseScale: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.05)' },
        },
        countUp: {
          from: { opacity: '0', transform: 'translateY(10px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      // Custom box shadows for consistent elevation
      boxShadow: {
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'card-hover': '0 12px 24px rgba(0, 0, 0, 0.3)',
        'glow-gold': '0 0 20px rgba(255, 215, 0, 0.5)',
        'glow-blue': '0 0 20px rgba(59, 130, 246, 0.5)',
      },
    },
  },
  plugins: [],
}

