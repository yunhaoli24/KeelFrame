import { expect, test } from "./fixtures";
import { login, waitForSuccessfulApiResponse } from "./helpers/app";

type PageItems<T> = {
  items: T[];
};

type SystemConfigItem = {
  key: string;
};

test("navigates authenticated app pages with real backend data", async ({ page }) => {
  await login(page);

  await expect(page.getByText("后台管理系统")).toBeVisible();
  await expect(page.getByRole("button", { name: /控制台/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: "workspace" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Overview" })).toBeVisible();

  await page.goto("/system/user");

  await expect(page).toHaveURL(/\/system\/user/);
  await expect(page.getByRole("heading", { name: "Users" })).toBeVisible();
  await expect(page.getByRole("button", { name: "New User" })).toBeVisible();
  await expect(page.getByText("admin").first()).toBeVisible();
  await expect(page.getByText("admin@example.com").first()).toBeVisible();

  await page.goto("/system/menu");

  await expect(page).toHaveURL(/\/system\/menu/);
  await expect(page.getByRole("heading", { name: "Menus" })).toBeVisible();
  await expect(page.getByRole("button", { name: "New Menu" })).toBeVisible();
  await expect(page.getByText("系统管理").first()).toBeVisible();
  await expect(page.getByText("用户管理").first()).toBeVisible();

  const initialResponse = await waitForSuccessfulApiResponse<PageItems<SystemConfigItem>>(
    page,
    "/sys/configs",
    () => page.goto("/system/config"),
  );
  expect(initialResponse.data?.items.length).toBeGreaterThan(0);

  await expect(page.getByRole("heading", { name: "System Configs" })).toBeVisible();
  await page.getByPlaceholder("Search by type").fill("LOGIN");

  const searchResponse = await waitForSuccessfulApiResponse<PageItems<SystemConfigItem>>(
    page,
    "/sys/configs",
    () => page.getByRole("button", { name: "Search", exact: true }).click(),
  );
  expect(searchResponse.data?.items.some((item) => item.key === "LOGIN_CAPTCHA_ENABLED")).toBe(
    true,
  );
  await expect(page.getByText("LOGIN_CAPTCHA_ENABLED")).toBeVisible();
});
