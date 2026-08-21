"use client";

import AdminNav from "@/components/site/AdminNav";
import AdminPlaceholder from "@/components/site/AdminPlaceholder";

export default function AdminPage() {
  return (
    <div className="space-y-4">
      <AdminNav />
      <AdminPlaceholder title="نقش‌ها و دسترسی" phase="فاز ۵ (کاربران)" note="مدیریت نقش از بخش «کاربران» انجام می‌شود." />
    </div>
  );
}
