import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";

export const metadata: Metadata = {
  title: "مقاله: تغذیه گیاه | اکو نوژین",
  description: "عناصر پرمصرف و کم‌مصرف — زمان و روش مصرف.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["learn/crops/nutrition"];
  return (
    <SitePage path="learn/crops/nutrition" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

    </SitePage>
  );
}
