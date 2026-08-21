"use client";

import ModelCatalog from "@/components/site/ModelCatalog";
import { PlatformPageHeader } from "@/components/site/PlatformPageHeader";

export default function ModelsPage() {
  return (
    <div className="mx-auto w-full max-w-6xl space-y-6 px-4 py-8">
      <PlatformPageHeader
        eyebrow="کتابخانه مدل‌های علمی"
        title="مدل‌های HyDroMa"
        description="مدل‌های هیدرولوژی، خاک، محصول، کربن و اقلیم با کارت اعتبار، محدودیت و مسیر اجرای شفاف."
        actionHref="/science"
        actionLabel="رفتن به لایه علم"
      />
      <ModelCatalog />
    </div>
  );
}
