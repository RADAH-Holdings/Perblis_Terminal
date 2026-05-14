"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";

const tabs = [
  { href: "/analytics", label: "Revenue" },
  { href: "/analytics/performance", label: "Performance" },
];

export default function AnalyticsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="space-y-6">
      <nav className="flex border-b border-border">
        {tabs.map((t) => {
          const active = pathname === t.href;
          return (
            <Link
              key={t.href}
              href={t.href}
              className={cn(
                "px-4 h-10 inline-flex items-center text-[13px] font-medium uppercase tracking-[0.06em] -mb-px",
                active
                  ? "text-forge border-b-2 border-forge"
                  : "text-text-secondary hover:text-text-primary",
              )}
            >
              {t.label}
            </Link>
          );
        })}
      </nav>
      {children}
    </div>
  );
}
