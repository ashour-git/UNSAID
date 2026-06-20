/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/templates/**/*.html"],
  theme: {
    extend: {
      colors: {
        canvas: "rgb(var(--c-canvas) / <alpha-value>)",
        paper: "rgb(var(--c-paper) / <alpha-value>)",
        shell: "rgb(var(--c-shell) / <alpha-value>)",
        text: "rgb(var(--c-text) / <alpha-value>)",
        mute: "rgb(var(--c-mute) / <alpha-value>)",
        soft: "rgb(var(--c-soft) / <alpha-value>)",
        metal: "rgb(var(--c-metal) / <alpha-value>)",
        line: "rgb(var(--c-line) / <alpha-value>)",
        stone: "rgb(var(--c-paper) / <alpha-value>)",
        parchment: "rgb(var(--c-paper) / <alpha-value>)",
        dark: "rgb(var(--c-shell) / <alpha-value>)",
        clay: "rgb(var(--c-mute) / <alpha-value>)",
        bronze: "rgb(var(--c-metal) / <alpha-value>)"
      },
      fontFamily: {
        display: ["Newsreader", "serif"],
        sans: ["Inter", "sans-serif"]
      },
      letterSpacing: {
        label: "0.14em",
        tight: "0.04em"
      }
    }
  }
};