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
  // Currently empty. Phase 2D's coverage check uses 0-orphan as a pass
  // criterion; allowlist entries are by-design orphans (not in the
  // inventory), so a separate "known-allowlist" exception list would be
  // needed to keep the coverage script clean. Re-introduce when that gap
  // is solved (e.g., by adding allowlist routes to the inventory directly).
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
