import SitePage from "@/components/site/SitePage";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Calculator } from "lucide-react";

const TOOLS = [
 [
  "irrigation",
  "نیاز آبیاری گیاه",
  "برآورد نیاز آبی با روش FAO-56 ساده‌شده (Kc × ETo)."
 ],
 [
  "compost-cn",
  "نسبت C/N کمپوست",
  "محاسبه نسبت کربن به نیتروژن مخلوط کاه و کود دامی."
 ],
 [
  "fertilizer",
  "نیاز کود نیتروژنه",
  "برآورد کود موردنیاز بر پایه نیاز گیاه و نیتروژن خاک."
 ],
 [
  "carbon-stock",
  "ذخیره کربن خاک",
  "محاسبه کربن آلی خاک و معادل CO₂ (روش IPCC)."
 ],
 [
  "erosion",
  "فرسایش خاک (RUSLE)",
  "برآورد فرسایش سالانه با معادله جهانی هدررفت خاک."
 ],
 [
  "water-footprint",
  "ردپای آب محصول",
  "حجم آب مصرفی به ازای هر تن محصول."
 ],
 [
  "seeding",
  "میزان بذر",
  "محاسبه بذر موردنیاز بر پایه تراکم و جوانه‌زنی."
 ],
 [
  "lime",
  "نیاز آهک",
  "برآورد آهک برای رساندن pH به بازه مطلوب."
 ],
 [
  "soil-water",
  "کمبود رطوبت خاک",
  "اختلاف رطوبت فعلی با ظرفیت مزرعه در عمق ریشه."
 ],
 [
  "drip-design",
  "طراحی قطره‌ای",
  "تعداد قطره‌چکان و دبی کل (ساده‌شده)."
 ],
 [
  "biomass",
  "زیست‌توده خشک",
  "تبدیل وزن تر به خشک با درصد رطوبت."
 ],
 [
  "co2-offset",
  "معادل CO₂",
  "تبدیل کربن به دی‌اکسیدکربن معادل (×3.67)."
 ]
];

export default function ToolsIndex() {
  return (
    <SitePage title="ابزارها و ماشین‌حساب‌ها" description="ماشین‌حساب‌های تخصصی کشاورزی با فرمول‌های مستند — برآوردهای آموزشی برای تصمیم‌گیری سریع." badge="ابزارها" related={["learn", "services/advisory", "help"]}>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {TOOLS.map(([id, title, desc]) => (
          <Link key={id} href={`/tools/${id}`} className="block">
            <Card className="h-full transition-shadow hover:shadow-md">
              <CardContent className="space-y-2 p-5">
                <p className="flex items-center gap-2 font-semibold text-foreground">
                  <Calculator className="h-4 w-4 text-primary" />
                  {title}
                </p>
                <p className="text-xs leading-6 text-muted-foreground">{desc}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </SitePage>
  );
}
