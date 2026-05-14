"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";

const tabs = [
  { href: "/settings", label: "Profile" },
  { href: "/settings/bank", label: "Bank" },
  { href: "/settings/notifications", label: "Notifications" },
  { href: "/settings/account", label: "Account" },
];

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="space-y-6">
      <nav className="flex border-b border-border overflow-x-auto tds-no-scrollbar">
        {tabs.map((t) => {
          const active = pathname === t.href;
          return (
            <Link
              key={t.href}
              href={t.href}
              className={cn(
                "px-4 h-10 inline-flex items-center text-[13px] font-medium uppercase tracking-[0.06em] -mb-px shrink-0",
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
