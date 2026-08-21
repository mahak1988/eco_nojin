"use client";

import AdminNav from "@/components/site/AdminNav";
import AdminPlaceholder from "@/components/site/AdminPlaceholder";

export default function AdminPage() {
  return (
    <div className="space-y-4">
      <AdminNav />
      <AdminPlaceholder title="تحلیل داده" phase="فاز ۷" note="مدل‌های علمی و تحلیل‌های DuckDB در فاز ۷ ارائه می‌شوند." />
    </div>
  );
}
