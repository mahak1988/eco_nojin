"use client";

import AdminUsers from "@/components/site/AdminUsers";

import AdminNav from "@/components/site/AdminNav";

export default function AdminUsersPage() {
  return (
    <div className="space-y-4">
      <AdminNav />
      <AdminUsers />
    </div>
  );
}
