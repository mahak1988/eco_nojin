"use client";

import AdminNav from "@/components/site/AdminNav";
import AdminPlaceholder from "@/components/site/AdminPlaceholder";

export default function AdminPage() {
  return (
    <div className="space-y-4">
      <AdminNav />
      <AdminPlaceholder title="ترجمه‌ها" phase="فاز ۶" note="ترجمه AI محتوا به ۱۴ زبان در فاز ۶ فعال می‌شود." />
    </div>
  );
}
