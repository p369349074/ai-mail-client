import type { Config } from 'tailwindcss';

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#172026',
        line: '#d7dde3',
        panel: '#f6f8fa',
        accent: '#0f766e',
      },
    },
  },
  plugins: [],
} satisfies Config;
