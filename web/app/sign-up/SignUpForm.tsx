"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { Logo } from "@/components/brand/Logo";

export function SignUpForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [orgName, setOrgName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, org_name: orgName || undefined })
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.error ?? "Registration failed. Please try again.");
      } else {
        router.push("/dashboard");
        router.refresh();
      }
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-brand-bg px-6">
      <div className="w-full max-w-[380px] rounded-[10px] border border-brand-border bg-brand-card p-8">
        <div className="mb-8 flex justify-center">
          <Logo size="md" showWordmark />
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-[12px] text-[#a1a1aa]">Email</label>
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="h-10 w-full rounded-[6px] border border-brand-border bg-brand-card px-3 text-[13px] text-white focus:outline-none focus:ring-1 focus:ring-brand-green"
            />
          </div>
          <div>
            <label className="mb-1 block text-[12px] text-[#a1a1aa]">Password</label>
            <input
              type="password"
              required
              autoComplete="new-password"
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="h-10 w-full rounded-[6px] border border-brand-border bg-brand-card px-3 text-[13px] text-white focus:outline-none focus:ring-1 focus:ring-brand-green"
            />
          </div>
          <div>
            <label className="mb-1 block text-[12px] text-[#a1a1aa]">
              Organisation name <span className="text-[#52525b]">(optional)</span>
            </label>
            <input
              type="text"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              placeholder="acme"
              className="h-10 w-full rounded-[6px] border border-brand-border bg-brand-card px-3 text-[13px] text-white placeholder:text-[#52525b] focus:outline-none focus:ring-1 focus:ring-brand-green"
            />
          </div>
          {error && <p className="text-[12px] text-red-400">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="h-10 w-full rounded-[6px] bg-white text-[13px] font-medium text-brand-bg hover:bg-white/90 disabled:opacity-50"
          >
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>
        <p className="mt-6 text-center text-[12px] text-[#52525b]">
          Already have an account?{" "}
          <Link href="/sign-in" className="text-[#a1a1aa] hover:text-white">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
