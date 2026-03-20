import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const isProtectedRoute = (pathname: string) => pathname.startsWith("/dashboard");

export default function middleware(req: NextRequest) {
  if (isProtectedRoute(req.nextUrl.pathname)) {
    const token = req.cookies.get("sf_token");
    if (!token) {
      return NextResponse.redirect(new URL("/sign-in", req.url));
    }
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next|.*\\..*).*)", "/"]
};
