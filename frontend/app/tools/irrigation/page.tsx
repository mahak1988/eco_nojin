import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import CalcTool from "@/components/site/CalcTool";

export const metadata: Metadata = {
  title: "ماشین‌حساب: نیاز آبیاری گیاه | اکو نوژین",
  description: "برآورد نیاز آبی با روش FAO-56 ساده‌شده (Kc × ETo).",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  return (
    <SitePage path="tools/irrigation" title="ماشین‌حساب: نیاز آبیاری گیاه" description="برآورد نیاز آبی با روش FAO-56 ساده‌شده (Kc × ETo)." badge="ماشین‌حساب" related={["tools", "learn/soil", "learn/water", "help"]}>

      <CalcTool id="irrigation" />
    </SitePage>
  );
}
