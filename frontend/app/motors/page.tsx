import type { Metadata } from "next";
import { MotorsDashboard } from "@/components/motors/motors-dashboard";

export const metadata: Metadata = {
  title: "موتورهای علمی | اکو نوژین",
  description: "موتورهای علمی اکو نوژین: SWAT+، AquaCrop، RothC، HEC-RAS و تحلیل سناریو",
};

export default function MotorsPage() {
  return (
    <div className="mx-auto w-full max-w-6xl space-y-6 px-4 py-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">موتورهای علمی</h1>
        <p className="mt-1 text-muted-foreground">
          شبیه‌سازی هیدرولوژی، محصول، کربن خاک، سیل و تحلیل سناریو با موتورهای علمی معتبر.
        </p>
      </div>
      <MotorsDashboard />
    </div>
  );
}
