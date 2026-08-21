import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import CalcTool from "@/components/site/CalcTool";

export const metadata: Metadata = {
  title: "ماشین‌حساب: ردپای آب محصول | اکو نوژین",
  description: "حجم آب مصرفی به ازای هر تن محصول.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  return (
    <SitePage path="tools/water-footprint" title="ماشین‌حساب: ردپای آب محصول" description="حجم آب مصرفی به ازای هر تن محصول." badge="ماشین‌حساب" related={["tools", "learn/soil", "learn/water", "help"]}>

      <CalcTool id="water-footprint" />
    </SitePage>
  );
}
