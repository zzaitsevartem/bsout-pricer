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
        clay: 'var(--color-danger)',
        'clay-ember': 'var(--color-danger-hover)',
        olive: 'var(--color-positive)',
        sky: '#6A9BCC',
        fig: '#C46686',
        cactus: '#BCD1CA',
        'green-discount': 'var(--color-discount)',
        'brand-green': '#00c078',
        accent: 'var(--color-accent)',
        'accent-hover': 'var(--color-accent-hover)',
        'featured-copy': 'var(--color-featured-copy)',
        'status-success': 'var(--color-success-surface)',
        'status-success-border': 'var(--color-success-border)',
        'status-success-text': 'var(--color-success-text)',
        'status-warning': 'var(--color-warning-surface)',
        'status-warning-border': 'var(--color-warning-border)',
        'status-warning-text': 'var(--color-warning-text)',
        'status-danger': 'var(--color-danger-surface)',
        'status-danger-border': 'var(--color-danger-border)',
        'status-danger-text': 'var(--color-danger-badge-text)',
        'status-info': 'var(--color-info-surface)',
        'status-info-border': 'var(--color-info-border)',
        'status-info-text': 'var(--color-info-text)',
        'stock-unavailable': 'var(--color-stock-unavailable)',
        'search-surface': 'var(--color-search-surface)',
        'search-row': 'var(--color-search-row)',
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
