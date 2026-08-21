"use client";

import AdminNav from "@/components/site/AdminNav";
import AdminErrors from "@/components/site/AdminErrors";

export default function AdminPage() {
  return (
    <div className="space-y-4">
      <AdminNav />
      <AdminErrors />
    </div>
  );
}
