// Routes that the crawler should also visit even though they're not in the
// pages inventory. Keep this list small — the inventory is the authoritative
// source.
//
// Use cases:
//   - 404 pages (deliberately invalid URL to capture v1's 404 chrome)
//   - Modal-only views accessible only via direct URL
//
// If you find yourself adding a route here that arguably belongs in the
// inventory, fix the inventory instead.

export interface AllowlistRoute {
  url: string;
  persona: string;       // canonical persona name
  description: string;   // human-readable why-it's-here
}

export const ROUTES_ALLOWLIST: AllowlistRoute[] = [
  // 404 chrome — deliberately invalid URL.
  {
    url: "/this-route-does-not-exist-on-purpose-for-the-catalog/",
    persona: "Agency Admin",
    description: "404 page chrome — not a real route",
  },
];

// HTTP methods + URL fragments that are permitted to leave the crawler.
// Anything not on this allowlist is aborted by Playwright's request
// interception (see crawl.ts). T4 of #107 — destructive-endpoint protection.
export const ALLOWED_NON_GET_FRAGMENTS: string[] = [
  "/dashboard/login/",
  "/dashboard/logout/",
  "/role-switch/",
  "/auth/magic-link/redeem/",
];
