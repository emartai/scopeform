import { beforeEach, describe, expect, it, vi } from "vitest";

const clerkMiddlewareMock = vi.fn((handler: unknown) => handler);
const createRouteMatcherMock = vi.fn(() => (req: { nextUrl?: { pathname?: string } }) => req.nextUrl?.pathname?.startsWith("/dashboard"));
const nextMock = vi.fn(() => "next-response");

vi.mock("@clerk/nextjs/server", () => ({
  clerkMiddleware: (handler: unknown) => clerkMiddlewareMock(handler),
  createRouteMatcher: (...args: unknown[]) => createRouteMatcherMock(...args)
}));

vi.mock("next/server", () => ({
  NextResponse: {
    next: () => nextMock()
  }
}));

describe("middleware", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = "pk_test_realish";
    process.env.CLERK_SECRET_KEY = "sk_test_realish";
  });

  it("protects dashboard routes when clerk is configured", async () => {
    const auth = { protect: vi.fn() };
    const request = { nextUrl: { pathname: "/dashboard" } };

    const module = await import("../middleware");
    const handler = module.default as (auth: typeof auth, req: typeof request) => Promise<unknown>;

    await handler(auth, request);

    expect(auth.protect).toHaveBeenCalledTimes(1);
  });

  it("skips auth when clerk env vars are missing", async () => {
    delete process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
    delete process.env.CLERK_SECRET_KEY;

    const auth = { protect: vi.fn() };
    const request = { nextUrl: { pathname: "/dashboard" } };

    const module = await import("../middleware");
    const handler = module.default as (auth: typeof auth, req: typeof request) => Promise<unknown>;

    const result = await handler(auth, request);

    expect(auth.protect).not.toHaveBeenCalled();
    expect(result).toBe("next-response");
  });
});
