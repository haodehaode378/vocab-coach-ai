/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js}',
  ],
  theme: {
    extend: {
      colors: {
        comic: {
          ink: '#1a1a1a',
          paper: '#fffef0',
          cream: '#fff8e1',
          pink: '#ff006e',
          blue: '#3a86ff',
          yellow: '#ffbe0b',
          green: '#06ffa5',
          orange: '#fb5607',
        }
      },
      fontFamily: {
        sans: ['system-ui', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['ui-monospace', 'Consolas', 'monospace'],
      },
      backgroundImage: {
        'halftone': 'radial-gradient(circle, #1a1a1a 1.5px, transparent 1.5px)',
      },
      backgroundSize: {
        'halftone': '12px 12px',
      },
    },
  },
  plugins: [],
}
