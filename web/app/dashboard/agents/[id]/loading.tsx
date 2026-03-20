export default function AgentDetailLoading() {
  return (
    <section>
      <div className="h-5 w-[80px] rounded bg-shimmer animate-shimmer" />
      <div className="mt-4 h-8 w-[220px] rounded bg-shimmer animate-shimmer" />
      <div className="mt-6 grid gap-5 xl:grid-cols-[minmax(0,55%)_minmax(0,45%)]">
        <div className="space-y-5">
          <div className="h-[300px] rounded-[8px] border border-brand-border bg-brand-card" />
          <div className="h-[180px] rounded-[8px] border border-brand-border bg-brand-card" />
        </div>
        <div className="space-y-5">
          <div className="h-[220px] rounded-[8px] border border-brand-border bg-brand-card" />
          <div className="h-[260px] rounded-[8px] border border-brand-border bg-brand-card" />
        </div>
      </div>
    </section>
  );
}
