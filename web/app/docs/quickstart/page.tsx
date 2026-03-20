import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Quickstart - Scopeform"
};

export default function QuickstartPage() {
  return (
    <div className="min-h-screen bg-brand-bg px-6 py-16 text-white">
      <div className="mx-auto max-w-[760px]">
        <h1 className="text-[20px] font-semibold text-white">Quickstart</h1>
        <p className="mt-3 text-[13px] text-[#a1a1aa]">
          Install Scopeform, authenticate the CLI, generate `scopeform.yml`, deploy your agent, and use the scoped runtime token in your app.
        </p>
        <div className="mt-6 space-y-5 text-[13px] text-[#a1a1aa]">
          <section>
            <h2 className="text-[14px] font-semibold text-white">1. Install</h2>
            <div className="mt-2 rounded-[6px] border border-brand-border bg-brand-card px-4 py-3 font-mono text-brand-green">
              <span className="text-[#52525b]">$ </span>
              pip install scopeform
            </div>
          </section>
          <section>
            <h2 className="text-[14px] font-semibold text-white">2. Log in</h2>
            <div className="mt-2 rounded-[6px] border border-brand-border bg-brand-card px-4 py-3 font-mono text-brand-green">
              <span className="text-[#52525b]">$ </span>
              scopeform login
            </div>
          </section>
          <section>
            <h2 className="text-[14px] font-semibold text-white">3. Initialise your project</h2>
            <div className="mt-2 rounded-[6px] border border-brand-border bg-brand-card px-4 py-3 font-mono text-brand-green">
              <span className="text-[#52525b]">$ </span>
              scopeform init
            </div>
          </section>
          <section>
            <h2 className="text-[14px] font-semibold text-white">4. Deploy</h2>
            <div className="mt-2 rounded-[6px] border border-brand-border bg-brand-card px-4 py-3 font-mono text-brand-green">
              <span className="text-[#52525b]">$ </span>
              scopeform deploy
            </div>
          </section>
          <section>
            <h2 className="text-[14px] font-semibold text-white">5. Use `SCOPEFORM_TOKEN`</h2>
            <p className="mt-2">
              Scopeform writes the runtime token to `.env`. Your agent should read `SCOPEFORM_TOKEN` from the environment rather than embedding a provider key directly.
            </p>
          </section>
          <section>
            <h2 className="text-[14px] font-semibold text-white">6. View the dashboard</h2>
            <p className="mt-2">
              Open `app.scopeform.dev` to inspect agent status, review logs, and revoke access.
            </p>
          </section>
        </div>
        <div className="mt-8 flex items-center gap-3">
          <Link
            href="/dashboard"
            className="inline-flex h-8 items-center rounded-[6px] bg-white px-3 text-[13px] font-medium text-brand-bg"
          >
            Open Dashboard
          </Link>
          <Link
            href="/sign-in"
            className="inline-flex h-8 items-center rounded-[6px] border border-brand-border px-3 text-[13px] text-[#a1a1aa]"
          >
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}
