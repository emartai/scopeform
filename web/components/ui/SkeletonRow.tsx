export function SkeletonRow() {
  return (
    <div className="flex h-12 items-center gap-4 border-b border-brand-border px-4">
      <div className="bg-shimmer h-4 w-[180px] animate-shimmer rounded" />
      <div className="bg-shimmer h-4 w-[140px] animate-shimmer rounded" />
      <div className="bg-shimmer h-4 w-[90px] animate-shimmer rounded" />
      <div className="bg-shimmer h-4 w-[110px] animate-shimmer rounded" />
      <div className="bg-shimmer ml-auto h-7 w-[88px] animate-shimmer rounded" />
    </div>
  );
}
