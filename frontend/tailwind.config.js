/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: '#050816',
          panel: '#0B112C',
          'panel-dark': '#070C22',
          card: 'rgba(11, 17, 44, 0.75)',
          border: 'rgba(46, 242, 197, 0.22)',
          'border-bright': '#2EF2C5',
          teal: '#2EF2C5',
          'teal-dim': 'rgba(46, 242, 197, 0.15)',
          cyan: '#00F0FF',
          blue: '#1A2955',
          muted: '#8A99AD',
          danger: '#FF3366',
          warning: '#FFB800',
        },
      },
      fontFamily: {
        heading: ['Orbitron', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
        sans: ['Inter', 'sans-serif'],
      },
      boxShadow: {
        'glow-teal': '0 0 15px rgba(46, 242, 197, 0.3)',
        'glow-teal-lg': '0 0 30px rgba(46, 242, 197, 0.45)',
        'glow-cyan': '0 0 20px rgba(0, 240, 255, 0.35)',
        'glow-card': '0 8px 32px 0 rgba(0, 0, 0, 0.45)',
      },
      animation: {
        'pulse-glow': 'pulseGlow 2.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'scanline': 'scanline 8s linear infinite',
        'radar': 'radarSweep 4s linear infinite',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': { opacity: '1', filter: 'drop-shadow(0 0 8px rgba(46, 242, 197, 0.6))' },
          '50%': { opacity: '0.6', filter: 'drop-shadow(0 0 2px rgba(46, 242, 197, 0.2))' },
        },
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(1000%)' },
        },
        radarSweep: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
      },
    },
  },
  plugins: [],
};
