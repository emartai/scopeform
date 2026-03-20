import { SkeletonRow } from "@/components/ui/SkeletonRow";

export default function LogsLoading() {
  return (
    <section>
      <div className="mb-5 h-8 w-[120px] rounded bg-shimmer animate-shimmer" />
      <div className="mb-5 flex gap-2">
        <div className="h-8 w-[170px] rounded bg-shimmer animate-shimmer" />
        <div className="h-8 w-[140px] rounded bg-shimmer animate-shimmer" />
        <div className="h-8 w-[140px] rounded bg-shimmer animate-shimmer" />
        <div className="h-8 w-[240px] rounded bg-shimmer animate-shimmer" />
      </div>
      <div className="overflow-hidden rounded-[8px] border border-brand-border">
        <div className="h-12 border-b border-brand-border bg-brand-card" />
        <SkeletonRow />
        <SkeletonRow />
        <SkeletonRow />
        <SkeletonRow />
        <SkeletonRow />
      </div>
    </section>
  );
}
