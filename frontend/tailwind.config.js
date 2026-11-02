/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: { extend: { colors: { navy: { 900: "#0b1b33", 800: "#12294a", 700: "#1b3a63" } } } },
  plugins: [],
};
