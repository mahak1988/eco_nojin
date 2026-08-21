import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";

export const metadata: Metadata = {
  title: "خدمت کربن و اقلیم | اکو نوژین",
  description: "مسیر ترسیب کربن خاک و گزارش‌دهی اقلیمی برای کشاورزی.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["services/carbon"];
  return (
    <SitePage path="services/carbon" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

    </SitePage>
  );
}
