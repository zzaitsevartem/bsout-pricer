import type { Config } from "tailwindcss"

const config: Config = {
  content: [
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        raleway: ['Raleway', 'DM Sans', 'system-ui', 'sans-serif'],
        'dm-sans': ['DM Sans', 'sans-serif'],
        lexend: ['Lexend', 'Georgia', 'serif'],
        montserrat: ['Montserrat', 'ui-monospace', 'monospace'],
      },
      colors: {
        ivory: '#FAF9F5',
        'ivory-elevated': '#F0EEE6',
        'ivory-warm': '#E3DACC',
        slate: '#141413',
        'slate-soft': '#1F1F1D',
        'slate-medium': '#282825',
        body: '#3D3D3A',
        'body-subtle': '#5E5D59',
        'body-muted': '#87867F',
        'border-default': '#B0AEA5',
        'border-light': '#E3DACC',
        'border-subtle': '#D1CFC5',
        'border-light-subtle': '#E8E6DC',
        clay: '#D97757',
        'clay-ember': '#C6613F',
        olive: '#788C5D',
        sky: '#6A9BCC',
        fig: '#C46686',
        cactus: '#BCD1CA',
        'green-discount': '#22c55e',
      },
      keyframes: {
        scroll: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' },
        },
        shimmer: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
      },
      animation: {
        scroll: 'scroll 20s linear infinite',
        shimmer: 'shimmer 4s linear infinite',
      },
    },
  },
  plugins: [],
}

export default config
