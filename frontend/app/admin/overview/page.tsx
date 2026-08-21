"use client";

import AdminNav from "@/components/site/AdminNav";
import AdminOverview from "@/components/site/AdminOverview";
import { Activity } from "lucide-react";
import { MotionSticker } from "@/components/ui/motion-sticker";

export default function AdminPage() {
  return (
    <div className="space-y-4">
      <AdminNav />
      <div className="flex justify-end">
        <MotionSticker label="پایش سامانه فعال" icon={Activity} tone="blue" />
      </div>
      <AdminOverview />
    </div>
  );
}
