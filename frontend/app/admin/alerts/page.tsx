"use client";

import AdminNav from "@/components/site/AdminNav";
import AdminPlaceholder from "@/components/site/AdminPlaceholder";

export default function AdminPage() {
  return (
    <div className="space-y-4">
      <AdminNav />
      <AdminPlaceholder title="هشدارهای پیشرفته" phase="فاز ۲ (پایه) + فاز ۷" note="ارزیابی NDVI واقعی در حلقه هشدار فعال است؛ داشبورد کامل هشدارها در فاز ۷." />
    </div>
  );
}
