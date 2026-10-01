import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: 'class',
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
        ivory: 'var(--color-ivory)',
        'ivory-elevated': 'var(--color-ivory-elevated)',
        'ivory-warm': 'var(--color-ivory-warm)',
        slate: 'var(--color-slate)',
        'slate-soft': 'var(--color-slate-soft)',
        'slate-medium': 'var(--color-slate-medium)',
        body: 'var(--color-body)',
        'body-subtle': 'var(--color-body-subtle)',
        'body-muted': 'var(--color-body-muted)',
        'border-default': 'var(--color-border-default)',
        'border-input': 'var(--color-border-input)',
        'border-light': 'var(--color-border-light)',
        'border-subtle': 'var(--color-border-subtle)',
        'border-light-subtle': 'var(--color-border-light-subtle)',
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
