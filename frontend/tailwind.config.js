/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#070d1a',
        panel: '#0f1729',
        glass: 'rgba(255,255,255,0.08)',
        danger: '#ef4444',
        accent: '#22d3ee',
      },
      boxShadow: {
        glow: '0 0 35px rgba(34,211,238,0.22)',
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
