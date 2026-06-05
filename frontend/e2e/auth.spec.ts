import { expect, test } from "./fixtures";
import { displayName, login } from "./helpers/app";

test("redirects protected routes to sign in and preserves the target route", async ({ page }) => {
  await page.goto("/system/user");

  await expect(page).toHaveURL(/\/auth\/sign-in\?redirect=\/system\/user/);
  await expect(page.getByRole("heading", { name: "Login" })).toBeVisible();
});

test("authenticates against the real backend and can log out", async ({ page }) => {
  await login(page);

  await expect(page.getByText(displayName)).toBeVisible();
  await page.getByText(displayName).click();
  await page.getByRole("menuitem", { name: "Log out" }).click();

  await expect(page).toHaveURL(/\/auth\/sign-in/);
  await expect(page.getByRole("heading", { name: "Login" })).toBeVisible();
});
