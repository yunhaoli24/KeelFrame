import { defineConfig, devices } from "@playwright/test";

const apiURL = process.env.E2E_API_URL ?? "http://localhost:8080";
const isCI = Boolean(process.env.CI);
const coverageEnabled = process.env.E2E_COVERAGE === "true";
const defaultFrontendPort = coverageEnabled ? "5174" : "5173";
const baseURL = process.env.E2E_BASE_URL ?? `http://localhost:${defaultFrontendPort}`;
const frontendPort = new URL(baseURL).port || defaultFrontendPort;

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  fullyParallel: false,
  forbidOnly: isCI,
  retries: 0,
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  expect: {
    timeout: 15_000,
  },
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  webServer: {
    command: `VITE_SERVER_API_URL=${baseURL} VITE_SERVER_API_PREFIX=/api/v1 VITE_PROXY_API_URL=${apiURL} VITE_COVERAGE=${coverageEnabled ? "true" : "false"} pnpm exec vp dev --host --port ${frontendPort}`,
    url: baseURL,
    reuseExistingServer: !isCI && !coverageEnabled,
    timeout: 120_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
