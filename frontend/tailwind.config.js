/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#8b7355',
        'primary-dark': '#6d5a43',
        'primary-light': '#a08876',
        cream: '#f9f7f4',
        beige: '#e8ddd3',
        'beige-dark': '#d4c4b0',
        elegant: '#ffe5d9',
      },
      fontFamily: {
        serif: ['Cormorant Garamond', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
}
