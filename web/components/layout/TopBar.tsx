"use client";

import { UserButton } from "@clerk/nextjs";
import { usePathname } from "next/navigation";

const breadcrumbMap: Record<string, string> = {
  "/dashboard": "Dashboard / Agents",
  "/dashboard/logs": "Dashboard / Logs",
  "/dashboard/settings": "Dashboard / Settings"
};

export function TopBar() {
  const pathname = usePathname();
  const breadcrumb = Object.entries(breadcrumbMap).find(([key]) => pathname.startsWith(key))?.[1] ?? "Dashboard";
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

  return (
    <header className="sticky top-0 z-20 flex h-12 items-center justify-between border-b border-brand-border bg-brand-bg px-6">
      <div className="text-[13px] text-[#a1a1aa]">{breadcrumb}</div>
      <div className="flex items-center gap-3">
        <span className="text-[13px] text-white">Scopeform Org</span>
        {publishableKey ? (
          <UserButton
            appearance={{
              elements: {
                avatarBox: "h-7 w-7"
              }
            }}
          />
        ) : (
          <div className="h-7 w-7 rounded-full border border-brand-border bg-brand-card" />
        )}
      </div>
    </header>
  );
}
