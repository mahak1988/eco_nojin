import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import CalcTool from "@/components/site/CalcTool";

export const metadata: Metadata = {
  title: "ماشین‌حساب: کمبود رطوبت خاک | اکو نوژین",
  description: "اختلاف رطوبت فعلی با ظرفیت مزرعه در عمق ریشه.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  return (
    <SitePage path="tools/soil-water" title="ماشین‌حساب: کمبود رطوبت خاک" description="اختلاف رطوبت فعلی با ظرفیت مزرعه در عمق ریشه." badge="ماشین‌حساب" related={["tools", "learn/soil", "learn/water", "help"]}>

      <CalcTool id="soil-water" />
    </SitePage>
  );
}
