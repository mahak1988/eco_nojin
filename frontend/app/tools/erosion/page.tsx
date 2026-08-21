import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import CalcTool from "@/components/site/CalcTool";

export const metadata: Metadata = {
  title: "ماشین‌حساب: فرسایش خاک (RUSLE) | اکو نوژین",
  description: "برآورد فرسایش سالانه با معادله جهانی هدررفت خاک.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  return (
    <SitePage path="tools/erosion" title="ماشین‌حساب: فرسایش خاک (RUSLE)" description="برآورد فرسایش سالانه با معادله جهانی هدررفت خاک." badge="ماشین‌حساب" related={["tools", "learn/soil", "learn/water", "help"]}>

      <CalcTool id="erosion" />
    </SitePage>
  );
}
