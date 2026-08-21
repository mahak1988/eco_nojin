import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";
import Quiz from "@/components/site/Quiz";

export const metadata: Metadata = {
  title: "آموزش: کربن | اکو نوژین",
  description: "چرخه کربن، ترسیب در خاک و گزارش‌دهی.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["learn/carbon"];
  return (
    <SitePage path="learn/carbon" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

      <Quiz category="carbon" />
    </SitePage>
  );
}
