import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      colors: {
        canvas: '#060b14',
        surface: 'rgba(14, 20, 31, 0.88)',
        elevated: 'rgba(24, 32, 48, 0.94)',
        subtle: '#8c98ad',
        default: '#d6deed',
        strong: '#f8fbff',
        muted: 'rgba(255, 255, 255, 0.16)',
        border: {
          subtle: 'rgba(255, 255, 255, 0.36)',
          default: 'rgba(255, 255, 255, 0.48)',
        },
        primary: {
          600: '#5b8cff',
        },
        success: {
          500: '#22c55e',
        },
        warning: {
          500: '#f59e0b',
        },
      },
      borderRadius: {
        card: '12px',
        control: '8px',
        utility: '4px',
      },
      spacing: {
        1: '4px',
        2: '8px',
        3: '12px',
        4: '16px',
        6: '24px',
        8: '32px',
        10: '40px',
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', '"Inter"', '"Avenir Next"', 'sans-serif'],
      },
      transitionDuration: {
        150: '150ms',
      },
      transitionTimingFunction: {
        industrial: 'ease-in-out',
      },
      maxWidth: {
        shell: '1680px',
      },
    },
  },
} satisfies Config
