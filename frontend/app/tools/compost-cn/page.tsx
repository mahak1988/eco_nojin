import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import CalcTool from "@/components/site/CalcTool";

export const metadata: Metadata = {
  title: "ماشین‌حساب: نسبت C/N کمپوست | اکو نوژین",
  description: "محاسبه نسبت کربن به نیتروژن مخلوط کاه و کود دامی.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  return (
    <SitePage path="tools/compost-cn" title="ماشین‌حساب: نسبت C/N کمپوست" description="محاسبه نسبت کربن به نیتروژن مخلوط کاه و کود دامی." badge="ماشین‌حساب" related={["tools", "learn/soil", "learn/water", "help"]}>

      <CalcTool id="compost-cn" />
    </SitePage>
  );
}
