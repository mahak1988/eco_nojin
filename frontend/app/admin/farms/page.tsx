"use client";

import AdminNav from "@/components/site/AdminNav";
import AdminFarms from "@/components/site/AdminFarms";

export default function AdminPage() {
  return (
    <div className="space-y-4">
      <AdminNav />
      <AdminFarms />
    </div>
  );
}
