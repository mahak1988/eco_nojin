import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";

export const metadata: Metadata = {
  title: "بازار — نمای کلی | اکو نوژین",
  description: "بازار محصولات و نهاده‌های کشاورزی.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["modules/marketplace/overview"];
  return (
    <SitePage path="modules/marketplace/overview" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

    </SitePage>
  );
}
