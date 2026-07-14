/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        offwhite: "#FAF7F2",
        brown: {
          light: "#A9744F",
          DEFAULT: "#7B4B2A",
          dark: "#4E2F1B",
        },
      },
      borderRadius: {
        card: "16px",
      },
    },
  },
  plugins: [],
}
