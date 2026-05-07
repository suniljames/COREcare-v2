import { describe, it, expect } from "vitest";
import { isBlockedHost, BLOCKED_HOSTS } from "../crawl.ts";

describe("isBlockedHost", () => {
  it("blocks the production .elitecare. wildcard", () => {
    expect(isBlockedHost("https://app.elitecare.bayareaelitehomecare.com")).toBe(true);
    expect(isBlockedHost("https://prod.elitecare.io")).toBe(true);
  });

  it("blocks the bayareaelitehomecare.com host literally", () => {
    expect(isBlockedHost("https://bayareaelitehomecare.com")).toBe(true);
    expect(isBlockedHost("https://www.bayareaelitehomecare.com/login")).toBe(true);
  });

  it("blocks corecare.app (v2 production)", () => {
    expect(isBlockedHost("https://corecare.app")).toBe(true);
    expect(isBlockedHost("https://api.corecare.app/healthz")).toBe(true);
  });

  it("is case-insensitive", () => {
    expect(isBlockedHost("https://BAYAREAelitehomecare.com")).toBe(true);
    expect(isBlockedHost("https://CoreCare.App")).toBe(true);
  });

  it("does NOT block localhost-shaped URLs", () => {
    expect(isBlockedHost("http://localhost:8000")).toBe(false);
    expect(isBlockedHost("http://127.0.0.1:8000/dashboard/login/")).toBe(false);
    expect(isBlockedHost("http://0.0.0.0:8000")).toBe(false);
  });

  it("does NOT block arbitrary non-prod hosts", () => {
    expect(isBlockedHost("http://test.dev")).toBe(false);
    expect(isBlockedHost("https://example.com")).toBe(false);
  });

  it("BLOCKED_HOSTS is a non-empty array of regexes", () => {
    expect(BLOCKED_HOSTS.length).toBeGreaterThan(0);
    BLOCKED_HOSTS.forEach((re) => expect(re).toBeInstanceOf(RegExp));
  });
});
