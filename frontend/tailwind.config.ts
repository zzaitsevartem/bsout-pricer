import type { Config } from "tailwindcss"

const config: Config = {
  content: [
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-sans)', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
        serif: ['var(--font-serif)', 'Georgia', 'serif'],
      },
      colors: {
        'page-base': '#FAF9F5',
        'surface-elevated': '#F0EEE6',
        'surface-warm-card': '#E3DACC',
        'surface-feature-dark': '#141413',
        heading: '#141413',
        body: '#3D3D3A',
        'body-subtle': '#5E5D59',
        'body-muted': '#87867F',
        slate: '#141413',
        'slate-medium': '#3D3D3A',
        clay: '#D97757',
        'clay-ember': '#C6613F',
        gray: '#87867F',
      },
      backgroundImage: {
        'hero-gradient': 'linear-gradient(190deg, #FAF9F5 55%, #5E5D59 100%)',
      },
      keyframes: {
        smoothGlow: {
          '0%': { boxShadow: '4px 0 6px 2px rgba(255,50,180,.5), 0 4px 6px 2px rgba(255,200,0,.2), -4px 0 6px 2px rgba(0,200,0,.15), 0 -4px 6px 2px rgba(100,200,255,.3)' },
          '25%': { boxShadow: '0 4px 6px 2px rgba(255,50,180,.5), -4px 0 6px 2px rgba(255,200,0,.2), 0 -4px 6px 2px rgba(0,200,0,.15), 4px 0 6px 2px rgba(100,200,255,.3)' },
          '50%': { boxShadow: '-4px 0 6px 2px rgba(255,50,180,.5), 0 -4px 6px 2px rgba(255,200,0,.2), 4px 0 6px 2px rgba(0,200,0,.15), 0 4px 6px 2px rgba(100,200,255,.3)' },
          '75%': { boxShadow: '0 -4px 6px 2px rgba(255,50,180,.5), 4px 0 6px 2px rgba(255,200,0,.2), 0 4px 6px 2px rgba(0,200,0,.15), -4px 0 6px 2px rgba(100,200,255,.3)' },
          '100%': { boxShadow: '4px 0 6px 2px rgba(255,50,180,.5), 0 4px 6px 2px rgba(255,200,0,.2), -4px 0 6px 2px rgba(0,200,0,.15), 0 -4px 6px 2px rgba(100,200,255,.3)' },
        },
        scroll: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-33.333%)' },
        },
      },
      animation: {
        smoothGlow: 'smoothGlow 4s linear infinite',
        scroll: 'scroll 20s linear infinite',
      },
    },
  },
  plugins: [],
}

export default config
