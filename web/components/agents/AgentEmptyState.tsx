"use client";

export function AgentEmptyState() {
  return (
    <div className="flex min-h-[320px] flex-col items-center justify-center px-6 text-center">
      <p className="text-[13px] text-[#a1a1aa]">No agents registered yet.</p>
      <div className="mt-4 rounded-[6px] border border-brand-border bg-brand-card px-4 py-3 font-mono text-[13px] text-brand-green">
        <span className="mr-2 text-[#52525b]">$</span>
        scopeform deploy
      </div>
    </div>
  );
}
