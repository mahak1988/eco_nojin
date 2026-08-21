"use client";

import AdminNav from "@/components/site/AdminNav";
import AdminPlaceholder from "@/components/site/AdminPlaceholder";

export default function AdminPage() {
  return (
    <div className="space-y-4">
      <AdminNav />
      <AdminPlaceholder title="مستندات" phase="دائمی" note="مستندات در docs/en و پورتال دانش عمومی در دسترس است." />
    </div>
  );
}
