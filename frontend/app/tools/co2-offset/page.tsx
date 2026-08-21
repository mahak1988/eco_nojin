import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import CalcTool from "@/components/site/CalcTool";

export const metadata: Metadata = {
  title: "ماشین‌حساب: معادل CO₂ | اکو نوژین",
  description: "تبدیل کربن به دی‌اکسیدکربن معادل (×3.67).",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  return (
    <SitePage path="tools/co2-offset" title="ماشین‌حساب: معادل CO₂" description="تبدیل کربن به دی‌اکسیدکربن معادل (×3.67)." badge="ماشین‌حساب" related={["tools", "learn/soil", "learn/water", "help"]}>

      <CalcTool id="co2-offset" />
    </SitePage>
  );
}
