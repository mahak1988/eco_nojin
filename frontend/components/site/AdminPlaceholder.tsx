"use client";

import { Construction } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

/**
 * Honest placeholder for /admin sections that belong to later phases
 * (replaces the misleading generic content-page placeholders).
 */
export default function AdminPlaceholder({
  title,
  phase,
  note,
}: {
  title: string;
  phase: string;
  note?: string;
}) {
  return (
    <Card className="border-dashed">
      <CardContent className="flex flex-col items-center gap-3 p-10 text-center">
        <Construction className="h-10 w-10 text-muted-foreground" />
        <p className="text-lg font-bold text-foreground">{title}</p>
        <p className="text-sm text-muted-foreground">
          این ماژول در <span className="font-semibold text-foreground">{phase}</span> پیاده‌سازی می‌شود.
        </p>
        {note ? <p className="text-xs text-muted-foreground">{note}</p> : null}
      </CardContent>
    </Card>
  );
}
