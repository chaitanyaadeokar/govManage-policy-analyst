/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0f172a",
        card: "rgba(30, 41, 59, 0.7)",
        cardBorder: "rgba(255, 255, 255, 0.1)",
        primary: "#3b82f6",
        primaryHover: "#2563eb",
        textPrimary: "#f8fafc",
        textSecondary: "#94a3b8"
      }
    },
  },
  plugins: [],
}
