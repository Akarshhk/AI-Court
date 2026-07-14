/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        serif: ['Merriweather', 'serif'],
      },
      colors: {
        judge: '#a855f7', // purple-500
        prosecution: '#ef4444', // red-500
        defense: '#3b82f6', // blue-500
        juror: '#10b981', // emerald-500
        clerk: '#64748b', // slate-500
      }
    },
  },
  plugins: [],
}
