import { expect, test as base } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

type IstanbulCoverage = Record<string, unknown>;
type DiagnosticEntry = {
  type: string;
  text: string;
};
type ApiResponseDiagnostic = {
  code?: unknown;
  msg?: unknown;
  data?: unknown;
};

declare global {
  interface Window {
    __coverage__?: IstanbulCoverage;
  }
}

function coverageFileName(testTitle: string, workerIndex: number): string {
  const normalizedTitle = testTitle
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "")
    .slice(0, 100);

  return `playwright-${workerIndex}-${normalizedTitle || "test"}.json`;
}

function formatDiagnosticValue(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (value === null || value === undefined) {
    return String(value);
  }
  return JSON.stringify(value) ?? "[unserializable]";
}

function formatApiDiagnosticDetails(pathName: string, body: ApiResponseDiagnostic): string {
  const details = [`code=${formatDiagnosticValue(body.code)}`];
  if (body.msg) {
    details.push(`msg=${formatDiagnosticValue(body.msg)}`);
  }
  if (pathName.endsWith("/auth/captcha") && body.data && typeof body.data === "object") {
    const captcha = body.data as { is_enabled?: unknown };
    details.push(`is_enabled=${formatDiagnosticValue(captcha.is_enabled)}`);
  }

  return details.join(" ");
}

function formatApiDiagnostic(
  method: string,
  pathName: string,
  status: number,
  details?: string,
): string {
  return [method, pathName, status, details].filter(Boolean).join(" ");
}

export const test = base.extend({
  page: async ({ page }, use, testInfo) => {
    const diagnostics: DiagnosticEntry[] = [];

    page.on("console", (message) => {
      diagnostics.push({
        type: `console:${message.type()}`,
        text: message.text(),
      });
    });
    page.on("pageerror", (error) => {
      diagnostics.push({
        type: "pageerror",
        text: error.message,
      });
    });
    page.on("response", (response) => {
      const url = new URL(response.url());
      if (!url.pathname.startsWith("/api/v1")) {
        return;
      }

      void response
        .json()
        .then((body: ApiResponseDiagnostic) => {
          diagnostics.push({
            type: "api",
            text: formatApiDiagnostic(
              response.request().method(),
              url.pathname,
              response.status(),
              formatApiDiagnosticDetails(url.pathname, body),
            ),
          });
        })
        .catch(() => {
          diagnostics.push({
            type: "api",
            text: formatApiDiagnostic(response.request().method(), url.pathname, response.status()),
          });
        });
    });

    await use(page);

    if (testInfo.status !== testInfo.expectedStatus) {
      const currentURL = page.url();
      console.info(
        [
          `E2E diagnostics for failed test: ${testInfo.title}`,
          `Current URL: ${currentURL}`,
          ...diagnostics.slice(-80).map((entry) => `[${entry.type}] ${entry.text}`),
        ].join("\n"),
      );
    }

    if (process.env.E2E_COVERAGE !== "true") {
      return;
    }

    const coverage = await page.evaluate(() => window.__coverage__).catch(() => undefined);
    if (!coverage || Object.keys(coverage).length === 0) {
      throw new Error("Expected Istanbul coverage data on window.__coverage__.");
    }

    const outputDir = path.join(process.cwd(), ".nyc_output");
    await mkdir(outputDir, { recursive: true });
    await writeFile(
      path.join(outputDir, coverageFileName(testInfo.title, testInfo.workerIndex)),
      JSON.stringify(coverage),
    );
  },
});

export { expect };
