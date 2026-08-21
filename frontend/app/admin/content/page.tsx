"use client";

import AdminNav from "@/components/site/AdminNav";
import AdminContent from "@/components/site/AdminContent";

export default function AdminPage() {
  return (
    <div className="space-y-4">
      <AdminNav />
      <AdminContent />
    </div>
  );
}
