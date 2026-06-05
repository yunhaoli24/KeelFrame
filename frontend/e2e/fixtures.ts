import { expect, test as base } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

type IstanbulCoverage = Record<string, unknown>;

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

export const test = base.extend({
  page: async ({ page }, use, testInfo) => {
    await use(page);

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
