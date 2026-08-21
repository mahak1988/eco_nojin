"use client";

import AdminModels from "@/components/site/AdminModels";

import AdminNav from "@/components/site/AdminNav";

export default function AdminModelsPage() {
  return (
    <div className="space-y-4">
      <AdminNav />
      <AdminModels />
    </div>
  );
}
