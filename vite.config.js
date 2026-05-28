"""
Vite 7 Configuration for BarberPro Frontend

Asset bundling and development server configuration.
"""

import { defineConfig } from "vite";
import tailwindcss from "tailwindcss";
import autoprefixer from "autoprefixer";

export default defineConfig({
  root: "./resources",
  base: "/static/",
  
  build: {
    outDir: "../public",
    emptyOutDir: true,
    sourcemap: true,
    minify: "terser",
    rollupOptions: {
      input: {
        main: "./resources/js/main.js",
        styles: "./resources/css/styles.css",
      },
      output: {
        entryFileNames: "js/[name].[hash].js",
        chunkFileNames: "js/[name].[hash].js",
        assetFileNames: (assetInfo) => {
          if (assetInfo.name.endsWith(".css")) {
            return "css/[name].[hash][extname]";
          }
          return "assets/[name].[hash][extname]";
        },
      },
    },
  },

  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: false,
    hmr: {
      host: "localhost",
      port: 5173,
    },
  },

  css: {
    postcss: {
      plugins: [
        tailwindcss,
        autoprefixer,
      ],
    },
  },

  resolve: {
    alias: {
      "@": "/resources/js",
      "@css": "/resources/css",
      "@img": "/resources/img",
    },
  },

  optimizeDeps: {
    include: ["alpinejs"],
  },
});
