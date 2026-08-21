import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";
import Quiz from "@/components/site/Quiz";

export const metadata: Metadata = {
  title: "آموزش: گیاهان زراعی | اکو نوژین",
  description: "تغذیه گیاه، تناوب و انتخاب رقم.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["learn/crops"];
  return (
    <SitePage path="learn/crops" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

      <Quiz category="crops" />
    </SitePage>
  );
}
