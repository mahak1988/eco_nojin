"use client";

import AdminNav from "@/components/site/AdminNav";
import AdminSecurity from "@/components/site/AdminSecurity";

export default function AdminPage() {
  return (
    <div className="space-y-4">
      <AdminNav />
      <AdminSecurity />
    </div>
  );
}
