import { test, expect } from "@playwright/test";
test("admin shell exposes bounded contexts", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page.getByRole("navigation", { name: "Primary" })).toContainText(
    "Evaluation",
  );
  await page.getByRole("link", { name: "Projects" }).click();
  await expect(page.getByRole("heading", { name: "Projects" })).toBeVisible();
});
