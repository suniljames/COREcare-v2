import { expect, test } from "@playwright/test";

test("home page renders the COREcare heading", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "COREcare v2" })).toBeVisible();
});
