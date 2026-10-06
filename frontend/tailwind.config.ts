import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1f2430",
        paper: "#fafaf7",
        brand: { DEFAULT: "#2f5d50", dark: "#1f4036" },
      },
    },
  },
  plugins: [],
};
export default config;
