"use client";

import { Suspense } from "react";
import FarmDetail from "@/components/site/FarmDetail";

export default function FarmDetailPage() {
  return (
    <Suspense fallback={<p className="p-8 text-sm text-muted-foreground">در حال بارگذاری…</p>}>
      <FarmDetail />
    </Suspense>
  );
}
