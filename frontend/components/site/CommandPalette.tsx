"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Home, Search } from "lucide-react";

import { siteRegistry } from "@/lib/site-registry";
import { useI18n } from "@/lib/i18n-context";
import { entryTitle } from "@/lib/site-i18n";
import {
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
} from "@/components/ui/command";

/** جستجوی سراسری با Ctrl+K / ⌘K — همه صفحات registry */
export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const { locale } = useI18n();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const entries = useMemo(() => Object.values(siteRegistry), []);

  const go = (path: string) => {
    setOpen(false);
    router.push(`/${path}`);
  };

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="جستجوی صفحات، ماژول‌ها و ابزارها… (Ctrl+K)" />
      <CommandList>
        <CommandEmpty>نتیجه‌ای یافت نشد</CommandEmpty>
        <CommandGroup heading="اصلی">
          <CommandItem onSelect={() => go("")}>
            <Home className="h-4 w-4" />
            خانه
          </CommandItem>
          <CommandItem onSelect={() => go("search")}>
            <Search className="h-4 w-4" />
            جستجو
          </CommandItem>
        </CommandGroup>
        <CommandGroup heading="صفحات">
          {entries.map((e) => (
            <CommandItem key={e.path} value={`${e.path} ${e.title}`} onSelect={() => go(e.path)}>
              <span className="line-clamp-1">{entryTitle(e.path, e.title, locale)}</span>
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
