"use client";

import AdminNav from "@/components/site/AdminNav";
import AdminBots from "@/components/site/AdminBots";

export default function AdminPage() {
  return (
    <div className="space-y-4">
      <AdminNav />
      <AdminBots />
    </div>
  );
}
