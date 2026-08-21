"use client";

import AdminNav from "@/components/site/AdminNav";
import AdminSettings from "@/components/site/AdminSettings";

export default function AdminPage() {
  return (
    <div className="space-y-4">
      <AdminNav />
      <AdminSettings />
    </div>
  );
}
