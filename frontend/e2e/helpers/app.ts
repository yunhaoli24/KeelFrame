import { type Locator, type Page } from "@playwright/test";

import { expect } from "../fixtures";

const apiURL = process.env.E2E_API_URL ?? "http://localhost:8080";
const username = process.env.E2E_USERNAME ?? "admin";
const password = process.env.E2E_PASSWORD ?? "123456";
export const displayName = process.env.E2E_DISPLAY_NAME ?? "用户666";

type BackendResponse<T> = {
  code: number | string;
  msg?: string;
  data?: T;
};

function isApiResponse(responseURL: string, pathSuffix: string): boolean {
  const url = new URL(responseURL);
  return url.pathname === `/api/v1${pathSuffix}`;
}

export async function expectBackendAvailable(page: Page): Promise<void> {
  const response = await page.request.get(`${apiURL}/openapi`);
  expect(response.ok(), `Expected backend OpenAPI to be available at ${apiURL}/openapi`).toBe(true);
}

export async function login(page: Page): Promise<void> {
  await expectBackendAvailable(page);
  const captchaResponsePromise = page.waitForResponse((response) => {
    return isApiResponse(response.url(), "/auth/captcha") && response.request().method() === "GET";
  });
  await page.goto("/auth/sign-in");
  await captchaResponsePromise;

  await expect(page.getByRole("heading", { name: "Login" })).toBeVisible();
  await page.getByLabel("Username").fill(username);
  await page.getByLabel("Password").fill(password);

  const captchaInput = page.getByLabel("Verification Code");
  if (await captchaInput.isVisible()) {
    throw new Error(
      "E2E login requires LOGIN_CAPTCHA_ENABLED=false on the real backend; tests do not mock captcha.",
    );
  }

  const loginResponsePromise = page.waitForResponse((response) => {
    return isApiResponse(response.url(), "/auth/login") && response.request().method() === "POST";
  });
  await page.getByRole("button", { name: "Login" }).click();
  const loginResponse = await loginResponsePromise;
  expect(loginResponse.ok(), "Expected real backend login request to succeed").toBe(true);

  await expect(page).toHaveURL(/\/dashboard/, { timeout: 15_000 });
  await expect(page.getByRole("heading", { name: "workspace" })).toBeVisible();
}

export async function waitForSuccessfulApiResponse<T>(
  page: Page,
  pathSuffix: string,
  action: () => Promise<unknown>,
): Promise<BackendResponse<T>> {
  const responsePromise = page.waitForResponse((res) => {
    return isApiResponse(res.url(), pathSuffix) && res.request().method() === "GET";
  });
  await action();
  const response = await responsePromise;
  expect(response.ok(), `Expected GET ${pathSuffix} to return a successful HTTP status`).toBe(true);

  const body = (await response.json()) as BackendResponse<T>;
  expect(Number(body.code), `Expected GET ${pathSuffix} to return backend code 200`).toBe(200);
  return body;
}

export async function navigateSidebarGroup(
  page: Page,
  groupName: RegExp,
  linkName: RegExp,
): Promise<Locator> {
  const link = page.getByRole("link", { name: linkName });
  if (!(await link.isVisible())) {
    await page.getByRole("button", { name: groupName }).click();
  }
  await expect(link).toBeVisible();
  await expect(link).toBeEnabled();
  return link;
}
