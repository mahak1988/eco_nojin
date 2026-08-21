import type { Metadata } from "next";
import { ScienceDashboard } from "@/components/science/science-dashboard";
import { PlatformPageHeader } from "@/components/site/PlatformPageHeader";

export const metadata: Metadata = {
  title: "لایه آکادمیک | اکو نوژین",
  description: "داشبورد علمی اکو نوژین: کاتالوگ دیتاست‌ها، استناد مدل‌ها و ابزارهای علم باز.",
};

export default function SciencePage() {
  return (
    <div className="mx-auto w-full max-w-6xl space-y-6 px-4 py-8">
      <PlatformPageHeader
        eyebrow="داده و علم باز"
        title="لایه آکادمیک"
        description="کاتالوگ دیتاست‌ها، استناد مدل‌ها و ابزارهای علمی HyDroMa با نمایش روشن وضعیت real، simulated و نیازمندی‌های هر منبع."
        actionHref="/models"
        actionLabel="مشاهده مدل‌ها"
      />
      <ScienceDashboard />
    </div>
  );
}
