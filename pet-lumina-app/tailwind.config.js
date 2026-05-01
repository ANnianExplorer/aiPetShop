/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#f1f4ef",
        "inverse-surface": "#2d312e",
        "tertiary-fixed-dim": "#c8c6c5",
        "surface-container": "#ecefea",
        "surface-variant": "#e0e3df",
        "surface-bright": "#f7faf5",
        "on-secondary": "#ffffff",
        "primary-fixed": "#cee9d6",
        "secondary": "#0060ab",
        "tertiary-container": "#9e9c9c",
        "surface-container-highest": "#e0e3df",
        "on-tertiary": "#ffffff",
        "outline": "#727973",
        "on-primary-fixed-variant": "#344c3e",
        "on-error-container": "#93000a",
        "on-background": "#191c1a",
        "primary": "#4b6455",
        "on-secondary-fixed": "#001c39",
        "surface-tint": "#4b6455",
        "surface": "#f7faf5",
        "surface-container-high": "#e6e9e4",
        "on-secondary-container": "#00325d",
        "on-tertiary-fixed": "#1c1b1b",
        "primary-fixed-dim": "#b2cdbb",
        "secondary-container": "#3d9bfe",
        "tertiary-fixed": "#e5e2e1",
        "secondary-fixed-dim": "#a3c9ff",
        "on-primary-container": "#22392c",
        "on-primary": "#ffffff",
        "secondary-fixed": "#d3e3ff",
        "outline-variant": "#c2c8c2",
        "on-surface-variant": "#424844",
        "error": "#ba1a1a",
        "tertiary": "#5f5e5e",
        "surface-dim": "#d8dbd6",
        "inverse-on-surface": "#eff2ed",
        "background": "#f7faf5",
        "on-primary-fixed": "#082014",
        "inverse-primary": "#b2cdbb",
        "primary-container": "#89a392",
        "on-secondary-fixed-variant": "#004882",
        "on-error": "#ffffff",
        "error-container": "#ffdad6",
        "on-tertiary-fixed-variant": "#474746",
        "on-tertiary-container": "#343434",
        "on-surface": "#191c1a"
      },
      borderRadius: {
        "DEFAULT": "0.25rem",
        "lg": "0.5rem",
        "xl": "0.75rem",
        "full": "9999px"
      },
      spacing: {
        "xl": "32px",
        "unit": "4px",
        "xs": "4px",
        "md": "16px",
        "lg": "24px",
        "container-padding": "20px",
        "card-gutter": "12px",
        "sm": "8px"
      },
      fontFamily: {
        "caption-sm": ["Be Vietnam Pro", "sans-serif"],
        "label-bold": ["Be Vietnam Pro", "sans-serif"],
        "headline-md": ["Plus Jakarta Sans", "sans-serif"],
        "title-sm": ["Plus Jakarta Sans", "sans-serif"],
        "display-lg": ["Plus Jakarta Sans", "sans-serif"],
        "body-md": ["Be Vietnam Pro", "sans-serif"]
      },
      fontSize: {
        "caption-sm": ["13px", {"lineHeight": "1.4", "fontWeight": "400"}],
        "label-bold": ["12px", {"lineHeight": "1.2", "letterSpacing": "0.05em", "fontWeight": "700"}],
        "headline-md": ["24px", {"lineHeight": "1.3", "fontWeight": "600"}],
        "title-sm": ["18px", {"lineHeight": "1.4", "fontWeight": "600"}],
        "display-lg": ["32px", {"lineHeight": "1.2", "letterSpacing": "-0.02em", "fontWeight": "700"}],
        "body-md": ["16px", {"lineHeight": "1.6", "fontWeight": "400"}]
      },
      animation: {
        "slide-up": "slideUp 0.3s ease-out",
        "fade-in": "fadeIn 0.5s ease-out",
      },
      keyframes: {
        slideUp: {
          '0%': { transform: 'translateY(100%)' },
          '100%': { transform: 'translateY(0)' }
        },
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        }
      }
    }
  },
  plugins: [],
}