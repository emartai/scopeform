import { beforeEach, describe, expect, it, vi } from "vitest";

const redirectMock = vi.fn((url: URL) => ({ type: "redirect", url: url.toString() }));
const nextMock = vi.fn(() => ({ type: "next" }));

vi.mock("next/server", () => ({
  NextResponse: {
    redirect: (url: URL) => redirectMock(url),
    next: () => nextMock()
  }
}));

function makeRequest(pathname: string, hasCookie = false) {
  return {
    nextUrl: { pathname },
    url: `http://localhost:3000${pathname}`,
    cookies: {
      get: (name: string) => (hasCookie && name === "sf_token" ? { value: "test-token" } : undefined)
    }
  };
}

describe("middleware", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
  });

  it("redirects unauthenticated users from dashboard to sign-in", async () => {
    const { default: middleware } = await import("../middleware");
    const req = makeRequest("/dashboard", false);
    middleware(req as never);
    expect(redirectMock).toHaveBeenCalledTimes(1);
    expect(redirectMock.mock.calls[0][0].toString()).toContain("/sign-in");
  });

  it("allows authenticated users to access dashboard", async () => {
    const { default: middleware } = await import("../middleware");
    const req = makeRequest("/dashboard", true);
    middleware(req as never);
    expect(redirectMock).not.toHaveBeenCalled();
    expect(nextMock).toHaveBeenCalledTimes(1);
  });

  it("allows unauthenticated users to access public routes", async () => {
    const { default: middleware } = await import("../middleware");
    const req = makeRequest("/sign-in", false);
    middleware(req as never);
    expect(redirectMock).not.toHaveBeenCalled();
    expect(nextMock).toHaveBeenCalledTimes(1);
  });

  it("allows unauthenticated users to access home", async () => {
    const { default: middleware } = await import("../middleware");
    const req = makeRequest("/", false);
    middleware(req as never);
    expect(redirectMock).not.toHaveBeenCalled();
    expect(nextMock).toHaveBeenCalledTimes(1);
  });
});
