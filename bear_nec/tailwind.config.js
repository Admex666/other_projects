/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        game: {
          city: "#dc2626",      // red
          desert: "#eab308",    // yellow
          mountain: "#16a34a",  // green
          water: "#0284c7",     // blue
        },
      },
    },
  },
  plugins: [],
}
