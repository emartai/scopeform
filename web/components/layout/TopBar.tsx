"use client";

import { usePathname, useRouter } from "next/navigation";

const breadcrumbMap: Record<string, string> = {
  "/dashboard": "Dashboard / Agents",
  "/dashboard/logs": "Dashboard / Logs",
  "/dashboard/settings": "Dashboard / Settings"
};

export function TopBar() {
  const pathname = usePathname();
  const router = useRouter();
  const breadcrumb = Object.entries(breadcrumbMap).find(([key]) => pathname.startsWith(key))?.[1] ?? "Dashboard";

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/sign-in");
    router.refresh();
  }

  return (
    <header className="sticky top-0 z-20 flex h-12 items-center justify-between border-b border-brand-border bg-brand-bg px-6">
      <div className="text-[13px] text-[#a1a1aa]">{breadcrumb}</div>
      <div className="flex items-center gap-3">
        <span className="text-[13px] text-white">Scopeform Org</span>
        <button
          onClick={handleLogout}
          className="h-7 rounded-[6px] border border-brand-border px-3 text-[12px] text-[#a1a1aa] hover:border-white/30 hover:text-white"
        >
          Sign out
        </button>
      </div>
    </header>
  );
}
