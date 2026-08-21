"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Bot,
  Cpu,
  FileText,
  Settings,
  ShieldAlert,
  Users,
} from "lucide-react";

const LINKS = [
  { href: "/admin/overview", label: "نمای کلی", icon: Activity },
  { href: "/admin/health", label: "سلامت", icon: Activity },
  { href: "/admin/users", label: "کاربران", icon: Users },
  { href: "/admin/content", label: "محتوا", icon: FileText },
  { href: "/admin/bots", label: "ربات‌ها", icon: Bot },
  { href: "/admin/errors", label: "خطاها", icon: ShieldAlert },
  { href: "/admin/settings", label: "تنظیمات", icon: Settings },
  { href: "/admin/models", label: "مدل‌ها", icon: Cpu },
  { href: "/admin/security", label: "امنیت", icon: ShieldAlert },
];

export default function AdminNav() {
  const pathname = usePathname();
  return (
    <nav className="flex flex-wrap gap-2 rounded-xl border border-border bg-muted/20 p-2">
      {LINKS.map(({ href, label, icon: Icon }) => {
        const active = pathname === href;
        return (
          <Link
            key={href}
            href={href}
            className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
              active
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
