import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import CalcTool from "@/components/site/CalcTool";

export const metadata: Metadata = {
  title: "ماشین‌حساب: نیاز کود نیتروژنه | اکو نوژین",
  description: "برآورد کود موردنیاز بر پایه نیاز گیاه و نیتروژن خاک.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  return (
    <SitePage path="tools/fertilizer" title="ماشین‌حساب: نیاز کود نیتروژنه" description="برآورد کود موردنیاز بر پایه نیاز گیاه و نیتروژن خاک." badge="ماشین‌حساب" related={["tools", "learn/soil", "learn/water", "help"]}>

      <CalcTool id="fertilizer" />
    </SitePage>
  );
}
