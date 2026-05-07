import { describe, it, expect } from "vitest";
import { shouldAllowRequest } from "../crawl.ts";

// shouldAllowRequest decides whether Playwright should `continue` or `abort`
// a request. It is the unit-testable kernel of crawl.ts's setupNetworkInterception
// function. T4 of #107 — destructive-endpoint protection — reduces to "what
// does this function return for each (method, url, v1BaseUrl) input?"

const V1 = "http://localhost:8000";

describe("shouldAllowRequest", () => {
  it("allows GETs to same-origin URLs", () => {
    expect(shouldAllowRequest({ method: "GET", url: `${V1}/dashboard/`, v1BaseUrl: V1 }))
      .toMatchObject({ allow: true });
    expect(shouldAllowRequest({ method: "GET", url: `${V1}/admin/clients/42/`, v1BaseUrl: V1 }))
      .toMatchObject({ allow: true });
  });

  it("allows GETs to cross-origin URLs that aren't on the production blocklist", () => {
    // The crawler may legitimately fetch fonts/CDN assets from third-party hosts.
    expect(shouldAllowRequest({ method: "GET", url: "https://fonts.googleapis.com/css", v1BaseUrl: V1 }))
      .toMatchObject({ allow: true });
  });

  it("blocks any request to a production-blocked host (even GET)", () => {
    expect(shouldAllowRequest({ method: "GET", url: "https://bayareaelitehomecare.com/", v1BaseUrl: V1 }))
      .toMatchObject({ allow: false, reason: "blocked-host" });
    expect(shouldAllowRequest({ method: "POST", url: "https://corecare.app/api/", v1BaseUrl: V1 }))
      .toMatchObject({ allow: false, reason: "blocked-host" });
  });

  it("allows non-GET methods that match an allowlist fragment (login)", () => {
    expect(shouldAllowRequest({ method: "POST", url: `${V1}/dashboard/login/`, v1BaseUrl: V1 }))
      .toMatchObject({ allow: true });
    expect(shouldAllowRequest({ method: "POST", url: `${V1}/dashboard/logout/`, v1BaseUrl: V1 }))
      .toMatchObject({ allow: true });
  });

  it("allows role-switch and magic-link redeem (other allowlisted POSTs)", () => {
    expect(shouldAllowRequest({ method: "POST", url: `${V1}/role-switch/`, v1BaseUrl: V1 }))
      .toMatchObject({ allow: true });
    expect(shouldAllowRequest({ method: "POST", url: `${V1}/auth/magic-link/redeem/abc/`, v1BaseUrl: V1 }))
      .toMatchObject({ allow: true });
  });

  it("blocks non-GET methods that are NOT on the allowlist", () => {
    // The destructive-endpoint guard's whole point.
    expect(shouldAllowRequest({ method: "POST", url: `${V1}/admin/clients/42/delete/`, v1BaseUrl: V1 }))
      .toMatchObject({ allow: false, reason: "non-get-not-allowlisted" });
    expect(shouldAllowRequest({ method: "DELETE", url: `${V1}/admin/clients/42/`, v1BaseUrl: V1 }))
      .toMatchObject({ allow: false, reason: "non-get-not-allowlisted" });
    expect(shouldAllowRequest({ method: "PUT", url: `${V1}/admin/clients/42/`, v1BaseUrl: V1 }))
      .toMatchObject({ allow: false, reason: "non-get-not-allowlisted" });
    expect(shouldAllowRequest({ method: "PATCH", url: `${V1}/admin/clients/42/`, v1BaseUrl: V1 }))
      .toMatchObject({ allow: false, reason: "non-get-not-allowlisted" });
  });

  it("returns the matched allowlist fragment in the result for allowlisted POSTs (audit trail)", () => {
    const r = shouldAllowRequest({
      method: "POST",
      url: `${V1}/dashboard/login/`,
      v1BaseUrl: V1,
    });
    expect(r.allow).toBe(true);
    expect(r.allowedByFragment).toBe("/dashboard/login/");
  });

  it("blocked-host check runs BEFORE the GET fast-path (a malicious page-script GET to prod is still blocked)", () => {
    // Defense-in-depth: even if the page tries to GET a production endpoint,
    // we still abort it. The hostname blocklist is the outer layer.
    const r = shouldAllowRequest({
      method: "GET",
      url: "https://corecare.app/api/users",
      v1BaseUrl: V1,
    });
    expect(r.allow).toBe(false);
    expect(r.reason).toBe("blocked-host");
  });
});
