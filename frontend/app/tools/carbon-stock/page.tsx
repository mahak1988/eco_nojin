import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import CalcTool from "@/components/site/CalcTool";

export const metadata: Metadata = {
  title: "ماشین‌حساب: ذخیره کربن خاک | اکو نوژین",
  description: "محاسبه کربن آلی خاک و معادل CO₂ (روش IPCC).",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  return (
    <SitePage path="tools/carbon-stock" title="ماشین‌حساب: ذخیره کربن خاک" description="محاسبه کربن آلی خاک و معادل CO₂ (روش IPCC)." badge="ماشین‌حساب" related={["tools", "learn/soil", "learn/water", "help"]}>

      <CalcTool id="carbon-stock" />
    </SitePage>
  );
}
