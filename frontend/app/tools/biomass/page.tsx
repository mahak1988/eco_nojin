import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import CalcTool from "@/components/site/CalcTool";

export const metadata: Metadata = {
  title: "ماشین‌حساب: زیست‌توده خشک | اکو نوژین",
  description: "تبدیل وزن تر به خشک با درصد رطوبت.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  return (
    <SitePage path="tools/biomass" title="ماشین‌حساب: زیست‌توده خشک" description="تبدیل وزن تر به خشک با درصد رطوبت." badge="ماشین‌حساب" related={["tools", "learn/soil", "learn/water", "help"]}>

      <CalcTool id="biomass" />
    </SitePage>
  );
}
