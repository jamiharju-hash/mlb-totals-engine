import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        signal: {
          'strong-bet': '#10b981',
          'small-bet': '#0ea5e9',
          pass: '#64748b',
          fade: '#f43f5e',
          positive: '#34d399',
          negative: '#fb7185',
          warning: '#fbbf24',
        },
        surface: {
          card: 'rgb(15 23 42 / 0.70)',
          panel: 'rgb(15 23 42 / 0.60)',
          error: 'rgb(69 10 10 / 0.40)',
        },
        chart: {
          positive: '#34d399',
          neutral: '#38bdf8',
          axis: '#94a3b8',
          grid: '#1e293b',
        },
        border: {
          primary: '#1e293b',
          subtle: '#334155',
        },
      },
      letterSpacing: {
        brand: '0.3em',
      },
    },
  },
  plugins: [],
};

export default config;
