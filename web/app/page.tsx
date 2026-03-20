import Link from "next/link";
import type { Metadata } from "next";

import { Logo } from "@/components/brand/Logo";

export const metadata: Metadata = {
  title: "Scopeform",
  description: "Identity and access management for AI agents"
};

export default function HomePage() {
  return (
    <div className="min-h-screen bg-brand-bg text-white">
      <header className="border-b border-brand-border bg-brand-bg">
        <div className="mx-auto flex h-14 max-w-[1200px] items-center justify-between px-6">
          <Logo size="md" showWordmark />
          <div className="flex items-center gap-3">
            <Link href="/sign-in" className="text-[13px] text-[#a1a1aa]">
              Login
            </Link>
            <Link
              href="/dashboard"
              className="inline-flex h-8 items-center rounded-[6px] bg-white px-3 text-[13px] font-medium text-brand-bg"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>
      <main className="mx-auto flex max-w-[1200px] flex-col items-center px-6 py-20 text-center">
        <Logo size="lg" showWordmark />
        <h1 className="mt-10 max-w-[640px] text-[48px] font-bold leading-[1.05] tracking-[-0.03em] text-white">
          Okta for AI agents
        </h1>
        <p className="mt-4 max-w-[640px] text-[18px] text-[#a1a1aa]">
          Register every agent, issue scoped short-lived tokens, and give security teams one place to monitor and revoke access.
        </p>
        <div className="mt-8 flex items-center gap-3">
          <Link
            href="/dashboard"
            className="inline-flex h-8 items-center rounded-[6px] bg-white px-3 text-[13px] font-medium text-brand-bg"
          >
            Get Started Free
          </Link>
          <Link
            href="/docs/quickstart"
            className="inline-flex h-8 items-center rounded-[6px] border border-brand-border px-3 text-[13px] text-[#a1a1aa]"
          >
            View Docs
          </Link>
        </div>
        <div className="mt-12 rounded-[6px] border border-brand-border bg-brand-card px-4 py-3 font-mono text-[13px]">
          <span className="text-[#52525b]">$ </span>
          <span className="text-brand-green">scopeform deploy</span>
        </div>
      </main>
    </div>
  );
}
