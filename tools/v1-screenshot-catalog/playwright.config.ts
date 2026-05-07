import type { PlaywrightTestConfig } from "playwright/test";

// One-shot tooling, not pytest-shaped — this config exists to lock the
// browser launch options the crawler uses. The crawler itself does not run
// under @playwright/test; it spawns Playwright directly. This file is here
// for any future test that wants to share launch options.

const config: PlaywrightTestConfig = {
  use: {
    headless: true,
    viewport: { width: 1440, height: 900 },
    ignoreHTTPSErrors: false,
    bypassCSP: false,
  },
  timeout: 10_000,
};

export default config;
