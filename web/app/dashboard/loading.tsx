import { SkeletonRow } from "@/components/ui/SkeletonRow";

export default function DashboardLoading() {
  return (
    <section>
      <div className="mb-5 flex items-center justify-between">
        <div className="h-8 w-[180px] rounded bg-shimmer animate-shimmer" />
        <div className="h-8 w-[140px] rounded bg-shimmer animate-shimmer" />
      </div>
      <div className="overflow-hidden rounded-[8px] border border-brand-border">
        <div className="h-9 border-b border-brand-border bg-brand-card" />
        <SkeletonRow />
        <SkeletonRow />
        <SkeletonRow />
        <SkeletonRow />
        <SkeletonRow />
      </div>
    </section>
  );
}
