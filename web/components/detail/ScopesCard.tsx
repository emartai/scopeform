import type { Agent } from "@/lib/api";

type ScopesCardProps = {
  scopes: Agent["scopes"];
};

export function ScopesCard({ scopes }: ScopesCardProps) {
  return (
    <section className="rounded-[8px] border border-brand-border bg-brand-card px-5 py-4">
      <h2 className="text-[11px] font-medium uppercase tracking-[0.04em] text-[#52525b]">Permitted scopes</h2>
      <div className="mt-4 space-y-3">
        {scopes.map((scope) =>
          scope.actions.map((action) => (
            <div key={`${scope.service}-${action}`} className="flex items-center gap-2 text-[11px] font-medium">
              <span className="rounded-[4px] border border-brand-border bg-brand-subtle px-2 py-1 font-mono text-white">
                {scope.service}
              </span>
              <span className="text-[#52525b]">→</span>
              <span className="rounded-[4px] border border-brand-border bg-brand-subtle px-2 py-1 font-mono text-white">
                {action}
              </span>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
