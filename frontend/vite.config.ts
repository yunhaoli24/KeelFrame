import tailwindcss from "@tailwindcss/vite";
import vue from "@vitejs/plugin-vue";
import vueJsx from "@vitejs/plugin-vue-jsx";
import { fileURLToPath, URL } from "node:url";
import { visualizer } from "rollup-plugin-visualizer";
import AutoImport from "unplugin-auto-import/vite";
import Component from "unplugin-vue-components/vite";
import VueRouter from "vue-router/vite";
import { defineConfig } from "vite-plus";
import istanbul from "vite-plugin-istanbul";
import vueDevTools from "vite-plugin-vue-devtools";
import Layouts from "vite-plugin-vue-layouts";

const RouteGenerateExclude = ["**/components/**", "**/layouts/**", "**/data/**", "**/types/**"];
const proxyApiURL = process.env.VITE_PROXY_API_URL ?? "http://localhost:8080";

export default defineConfig({
  plugins: [
    VueRouter({
      exclude: RouteGenerateExclude,
      dts: "src/route-map.d.ts",
    }),
    vue(),
    vueJsx(),
    vueDevTools(),
    tailwindcss(),
    istanbul({
      include: "src/**/*",
      exclude: ["node_modules", "e2e", "dist"],
      extension: [".js", ".ts", ".tsx", ".vue"],
      requireEnv: true,
    }),
    visualizer({ gzipSize: true, brotliSize: true }),
    Layouts({
      defaultLayout: "default",
    }),
    AutoImport({
      include: [/\.[tj]sx?$/, /\.vue$/],
      imports: ["vue", "vue-router"],
      dirs: ["src/composables/**/*.ts", "src/constants/**/*.ts", "src/stores/**/*.ts"],
      defaultExportByFilename: true,
      dts: "src/types/auto-import.d.ts",
    }),
    Component({
      dirs: ["src/components"],
      collapseSamePrefixes: true,
      directoryAsNamespace: true,
      dts: "src/types/auto-import-components.d.ts",
    }),
  ],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  oxc: {
    drop: {
      debugger: true,
    },
  },
  server: {
    proxy: {
      "/api/v1": {
        target: proxyApiURL,
        changeOrigin: true,
      },
    },
  },
  lint: {
    ignorePatterns: ["dist/**", "*.d.ts"],
    options: {
      typeAware: true,
      typeCheck: false,
    },
  },
  fmt: {
    ignorePatterns: ["dist/**", "*.d.ts"],
  },
  staged: {
    "*": "vp check --fix",
  },
});
