import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => null);
  if (!body?.email || !body?.password) {
    return NextResponse.json({ error: "Email and password are required." }, { status: 400 });
  }

  const backendRes = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: body.email,
      password: body.password,
      org_name: body.org_name ?? undefined
    })
  }).catch(() => null);

  if (!backendRes) {
    return NextResponse.json({ error: "Could not reach server. Please try again." }, { status: 503 });
  }

  if (!backendRes.ok) {
    if (backendRes.status === 409) {
      return NextResponse.json({ error: "An account with this email already exists." }, { status: 409 });
    }
    return NextResponse.json({ error: "Registration failed. Please try again." }, { status: backendRes.status });
  }

  const data = await backendRes.json();
  const response = NextResponse.json({ email: data.email }, { status: 201 });

  response.cookies.set("sf_token", data.token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 60 * 60 * 24, // 24 hours
    path: "/"
  });

  return response;
}
