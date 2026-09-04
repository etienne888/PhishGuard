/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['Sora', 'ui-sans-serif', 'system-ui', 'sans-serif']
      },
      colors: {
        ink: '#0B1C3C',
        brand: {
          50: '#eef4ff',
          100: '#dbe7ff',
          200: '#b9d1ff',
          300: '#8bb2ff',
          400: '#5a8dff',
          500: '#2f66f5',
          600: '#1e3a8a',
          700: '#182f6e',
          800: '#142654',
          900: '#101f42'
        },
        signal: {
          green: '#00843D',
          red: '#CE1126',
          yellow: '#FFC72C'
        }
      },
      boxShadow: {
        card: '0 1px 2px rgba(11,28,60,0.06), 0 8px 24px -8px rgba(11,28,60,0.12)',
        lift: '0 20px 40px -16px rgba(30,58,138,0.35)'
      },
      keyframes: {
        scan: {
          '0%': { backgroundPosition: '0 0' },
          '100%': { backgroundPosition: '0 100%' }
        },
        wordFade: {
          from: { opacity: 0, transform: 'translateY(15px)' },
          to: { opacity: 1, transform: 'translateY(0)' }
        },
        fadeUp: {
          from: { opacity: 0, transform: 'translateY(10px)' },
          to: { opacity: 1, transform: 'translateY(0)' }
        }
      },
      animation: {
        scan: 'scan 4s linear infinite',
        wordFade: 'wordFade 0.8s forwards',
        fadeUp: 'fadeUp 0.8s forwards'
      }
    }
  },
  plugins: []
}
