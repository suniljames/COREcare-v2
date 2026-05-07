import { describe, it, expect, vi } from "vitest";
import { retryWithBackoff } from "../crawl.ts";

// Phase 2A SWE SHOULD-FIX: 3-retry / 1s-3s-9s backoff on TimeoutError, no
// retry on other errors. This tests the wrapper in isolation; integration
// with captureRoute is covered by the full E2E run.

class TimeoutError extends Error {
  override name = "TimeoutError";
}

describe("retryWithBackoff", () => {
  it("returns the result on first success without sleeping", async () => {
    const fn = vi.fn(async () => "ok");
    const sleep = vi.fn(async () => {});
    const result = await retryWithBackoff(fn, { attempts: 3, baseMs: 1000, sleep });
    expect(result).toBe("ok");
    expect(fn).toHaveBeenCalledTimes(1);
    expect(sleep).not.toHaveBeenCalled();
  });

  it("retries on TimeoutError up to attempts-1 times then re-throws", async () => {
    const fn = vi.fn(async () => {
      throw new TimeoutError("timeout");
    });
    const sleep = vi.fn(async () => {});
    await expect(
      retryWithBackoff(fn, { attempts: 3, baseMs: 1000, sleep }),
    ).rejects.toThrow(/timeout/);
    expect(fn).toHaveBeenCalledTimes(3);
    expect(sleep).toHaveBeenCalledTimes(2); // sleeps between attempts, not after last
  });

  it("uses exponential backoff with the documented schedule (1s, 3s, 9s)", async () => {
    const sleeps: number[] = [];
    const fn = vi.fn(async () => {
      throw new TimeoutError("timeout");
    });
    const sleep = vi.fn(async (ms: number) => {
      sleeps.push(ms);
    });
    await expect(
      retryWithBackoff(fn, { attempts: 4, baseMs: 1000, sleep }),
    ).rejects.toThrow();
    // 4 attempts = 3 sleeps; 1s, 3s, 9s
    expect(sleeps).toEqual([1000, 3000, 9000]);
  });

  it("does NOT retry non-TimeoutError errors; rethrows immediately", async () => {
    const fn = vi.fn(async () => {
      throw new Error("permanent");
    });
    const sleep = vi.fn(async () => {});
    await expect(
      retryWithBackoff(fn, { attempts: 3, baseMs: 1000, sleep }),
    ).rejects.toThrow(/permanent/);
    expect(fn).toHaveBeenCalledTimes(1);
    expect(sleep).not.toHaveBeenCalled();
  });

  it("succeeds if a retry attempt returns successfully", async () => {
    let calls = 0;
    const fn = vi.fn(async () => {
      calls++;
      if (calls < 3) throw new TimeoutError("transient");
      return "eventually-ok";
    });
    const sleep = vi.fn(async () => {});
    const result = await retryWithBackoff(fn, { attempts: 3, baseMs: 1000, sleep });
    expect(result).toBe("eventually-ok");
    expect(fn).toHaveBeenCalledTimes(3);
    expect(sleep).toHaveBeenCalledTimes(2);
  });
});
