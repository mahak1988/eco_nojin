"use client";

import AdminNav from "@/components/site/AdminNav";
import AdminPlaceholder from "@/components/site/AdminPlaceholder";

export default function AdminPage() {
  return (
    <div className="space-y-4">
      <AdminNav />
      <AdminPlaceholder title="بکاپ و بازیابی" phase="فاز ۰ (اسکریپت) + فاز ۱۰" note="اسکریپت بکاپ موجود است؛ پنل مدیریت بکاپ در فاز ۱۰." />
    </div>
  );
}
