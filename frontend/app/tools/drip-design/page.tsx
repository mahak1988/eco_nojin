import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import CalcTool from "@/components/site/CalcTool";

export const metadata: Metadata = {
  title: "ماشین‌حساب: طراحی قطره‌ای | اکو نوژین",
  description: "تعداد قطره‌چکان و دبی کل (ساده‌شده).",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  return (
    <SitePage path="tools/drip-design" title="ماشین‌حساب: طراحی قطره‌ای" description="تعداد قطره‌چکان و دبی کل (ساده‌شده)." badge="ماشین‌حساب" related={["tools", "learn/soil", "learn/water", "help"]}>

      <CalcTool id="drip-design" />
    </SitePage>
  );
}
