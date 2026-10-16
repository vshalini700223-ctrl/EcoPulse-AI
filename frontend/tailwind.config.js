/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        forest: {
          950: '#041510',
          900: '#06251b',
          850: '#0a3024',
          800: '#0e3c2e',
          700: '#14513f',
          600: '#1c6a53',
          500: '#258468',
        },
        emerald: {
          400: '#34d399',
          500: '#10b981',
          600: '#059669',
        },
        teal: {
          400: '#2dd4bf',
          500: '#14b8a6',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        'eco-subtle': '0 4px 20px -2px rgba(6, 37, 27, 0.4)',
        'eco-glow': '0 0 25px -5px rgba(52, 211, 153, 0.15)',
      }
    },
  },
  plugins: [],
}
