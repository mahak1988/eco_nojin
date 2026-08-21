"use client";

import AdminNav from "@/components/site/AdminNav";
import AdminPlaceholder from "@/components/site/AdminPlaceholder";

export default function AdminPage() {
  return (
    <div className="space-y-4">
      <AdminNav />
      <AdminPlaceholder title="مدیریت داده" phase="فاز ۴/۹" note="خط لوله داده واقعی فعال است؛ مدیریت دیتاست در فاز ۹." />
    </div>
  );
}
