import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#18212b",
        paper: "#ffffff",
        brand: { DEFAULT: "#245447", dark: "#183c31" },
      },
    },
  },
  plugins: [],
};
export default config;
