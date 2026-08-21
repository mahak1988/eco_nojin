import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";

export const metadata: Metadata = {
  title: "خدمات اکو نوژین | اکو نوژین",
  description: "مجموعه کامل خدمات دانش‌بنیان برای کشاورزی اقلیم‌هوشمند، آب، خاک و کربن — از مشاوره تا بازار.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["services"];
  return (
    <SitePage path="services" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

    </SitePage>
  );
}
