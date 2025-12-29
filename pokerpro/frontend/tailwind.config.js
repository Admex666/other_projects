/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                poker: {
                    green: '#0D5E3A',
                    'green-light': '#1A7F4F',
                    'green-dark': '#083D26',
                    red: '#DC2626',
                    gold: '#F59E0B',
                    'gold-light': '#FCD34D',
                }
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
