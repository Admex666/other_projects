/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        jetlag: {
          light: '#f7d14c', // Yellowish
          DEFAULT: '#e6b91e', 
          dark: '#b89209',
        }
      }
    },
  },
  plugins: [],
}
