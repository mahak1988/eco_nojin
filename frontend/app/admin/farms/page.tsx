"use client";

import AdminNav from "@/components/site/AdminNav";
import AdminPlaceholder from "@/components/site/AdminPlaceholder";

export default function AdminPage() {
  return (
    <div className="space-y-4">
      <AdminNav />
      <AdminPlaceholder title="مزارع" phase="فاز ۳ (داشبورد کاربر)" note="مدیریت مزارع از داشبورد کاربر انجام می‌شود." />
    </div>
  );
}
