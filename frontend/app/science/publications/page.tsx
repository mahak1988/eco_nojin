import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";

export const metadata: Metadata = {
  title: "انتشارات | اکو نوژین",
  description: "مقالات و گزارش‌های علمی پلتفرم.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["science/publications"];
  return (
    <SitePage path="science/publications" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

    </SitePage>
  );
}
