import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Bathymetric ink — deep chart-blue base, not generic near-black
        abyss: "#070D18",
        hull: "#0B1524",
        panel: "#101E33",
        raised: "#16283F",
        hair: "#1E3554",
        hairlit: "#2C4A73",
        ink: {
          hi: "#E6EFFA",
          mid: "#9FB4CE",
          lo: "#61789A",
        },
        // Provenance language
        observed: "#4CC9E8",   // measured / satellite-derived
        inferred: "#F0A63C",   // AI analysis & recommendation
        entered: "#C7D6EA",    // user-supplied
        critical: "#FF5C6C",
        elevated: "#FF9A47",
        moderate: "#F5D160",
        nominal: "#3FD79A",
      },
      fontFamily: {
        display: ["var(--font-display)", "ui-sans-serif", "system-ui"],
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      fontSize: {
        micro: ["10px", { lineHeight: "14px", letterSpacing: "0.14em" }],
        tiny: ["11px", { lineHeight: "16px", letterSpacing: "0.06em" }],
      },
      borderRadius: { xl: "10px", "2xl": "14px" },
      boxShadow: {
        panel: "0 1px 0 0 rgba(255,255,255,0.03) inset, 0 18px 40px -24px rgba(0,0,0,0.9)",
        glow: "0 0 0 1px rgba(76,201,232,0.35), 0 0 28px -6px rgba(76,201,232,0.45)",
      },
      keyframes: {
        sweep: { "0%": { transform: "translateX(-100%)" }, "100%": { transform: "translateX(100%)" } },
        pulseRing: {
          "0%": { boxShadow: "0 0 0 0 rgba(240,166,60,0.45)" },
          "70%": { boxShadow: "0 0 0 10px rgba(240,166,60,0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(240,166,60,0)" },
        },
      },
      animation: {
        sweep: "sweep 1.6s linear infinite",
        pulseRing: "pulseRing 2s ease-out infinite",
      },
    },
  },
  plugins: [],
};
export default config;
