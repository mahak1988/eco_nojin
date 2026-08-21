import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import CalcTool from "@/components/site/CalcTool";

export const metadata: Metadata = {
  title: "ماشین‌حساب: میزان بذر | اکو نوژین",
  description: "محاسبه بذر موردنیاز بر پایه تراکم و جوانه‌زنی.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  return (
    <SitePage path="tools/seeding" title="ماشین‌حساب: میزان بذر" description="محاسبه بذر موردنیاز بر پایه تراکم و جوانه‌زنی." badge="ماشین‌حساب" related={["tools", "learn/soil", "learn/water", "help"]}>

      <CalcTool id="seeding" />
    </SitePage>
  );
}
