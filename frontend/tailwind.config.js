/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#080a0c',
          900: '#0c1013',
          850: '#11171b',
          800: '#171e23',
          700: '#222c33'
        },
        signal: {
          500: '#c8f06a',
          600: '#a8d44b'
        }
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'Consolas', 'monospace']
      },
      boxShadow: {
        panel: '0 18px 55px rgba(0, 0, 0, .2)'
      }
    }
  },
  plugins: []
};
