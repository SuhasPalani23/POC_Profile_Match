/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'dark-bg': '#0A0A0A',
        'dark-container': '#1A1A1A',
        'dark-border': '#2A2A2A',
        'primary-cyan': '#13EFB7',
        'primary-blue': '#0EA5E9',
        'text-primary': '#FFFFFF',
        'text-secondary': '#9CA3AF',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}