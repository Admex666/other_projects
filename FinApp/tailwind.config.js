/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "primary": "#c5c0ff",
        "secondary": "#4de082",
        "background": "#0d141d",
        "surface": "#0d141d",
        "surface-container": "#192029",
        "surface-variant": "#2e353f",
        "on-surface": "#dce3f0",
        "on-surface-variant": "#c8c4d7",
        "error": "#ffb4ab",
        "outline": "#928fa0",
      },
      fontFamily: {
        inter: ['Inter', 'sans-serif'],
      },
      spacing: {
        'container-margin': '20px',
        'gutter-md': '16px',
        'stack-lg': '24px',
        'stack-md': '12px',
        'stack-sm': '4px',
      },
    },
  },
  plugins: [],
}
