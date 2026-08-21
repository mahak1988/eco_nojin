import type { Metadata } from "next";
import AdminNav from "@/components/site/AdminNav";
import AdminOverview from "@/components/site/AdminOverview";

export const metadata: Metadata = {
  title: "پنل مدیریت | اکو نوژین",
  description: "نمای کلی پنل مدیریت اکو نوژین — آمار، رویدادها و خطاهای اخیر.",
};

export default function AdminPage() {
  return (
    <div className="space-y-4">
      <AdminNav />
      <AdminOverview />
    </div>
  );
}
