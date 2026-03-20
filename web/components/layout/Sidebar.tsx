"use client";

import type { Route } from "next";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { FileClock, LayoutGrid, Settings } from "lucide-react";

import { Logo } from "@/components/brand/Logo";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard" as Route, label: "Agents", icon: LayoutGrid },
  { href: "/dashboard/logs" as Route, label: "Logs", icon: FileClock },
  { href: "/dashboard/settings" as Route, label: "Settings", icon: Settings }
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <>
      <aside className="fixed inset-y-0 left-0 hidden w-[40px] border-r border-brand-border bg-brand-card px-1 py-4 md:block lg:hidden">
        <div className="mb-4 flex h-10 items-center justify-center border-b border-brand-border pb-4">
          <Logo size="sm" />
        </div>
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);

            return (
              <Link
                key={item.href}
                href={item.href}
                aria-label={item.label}
                className={cn(
                  "relative flex h-8 items-center justify-center rounded-md text-[13px]",
                  isActive
                    ? "bg-brand-subtle text-white"
                    : "text-[#a1a1aa] transition-colors hover:bg-brand-elevated hover:text-white"
                )}
              >
                {isActive ? <span className="absolute inset-y-1 left-0 w-[2px] rounded-full bg-brand-green" /> : null}
                <Icon className="h-[15px] w-[15px]" />
              </Link>
            );
          })}
        </nav>
      </aside>
      <aside className="fixed inset-y-0 left-0 hidden w-[240px] border-r border-brand-border bg-brand-card px-3 py-4 lg:block">
        <div className="mb-4 flex h-10 items-center border-b border-brand-border pb-4">
          <Logo size="lg" showWordmark />
        </div>
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "relative flex h-8 items-center gap-3 rounded-md px-2 text-[13px]",
                  isActive
                    ? "bg-brand-subtle text-white"
                    : "text-[#a1a1aa] transition-colors hover:bg-brand-elevated hover:text-white"
                )}
              >
                {isActive ? <span className="absolute inset-y-1 left-0 w-[2px] rounded-full bg-brand-green" /> : null}
                <Icon className="h-[15px] w-[15px]" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </aside>
    </>
  );
}
