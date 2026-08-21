"use client";

import AdminHealth from "@/components/site/AdminHealth";

import AdminNav from "@/components/site/AdminNav";

export default function AdminHealthPage() {
  return (
    <div className="space-y-4">
      <AdminNav />
      <AdminHealth />
    </div>
  );
}
