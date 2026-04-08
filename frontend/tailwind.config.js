/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#f8fafc", 
        panel: "#ffffff",
        panelBorder: "#e2e8f0", 
        primary: "#1e40af", 
        primaryHover: "#1d4ed8", 
        textPrimary: "#0f172a", 
        textSecondary: "#64748b", 
        danger: "#dc2626",
        success: "#16a34a",
      }
    },
  },
  plugins: [],
}
