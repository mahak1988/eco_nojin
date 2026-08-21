import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";

export const metadata: Metadata = {
  title: "بحران آب و کشاورزی | اکو نوژین",
  description: "چگونه با مدیریت صحیح آبیاری، بحران آب را مهار کنیم؟",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["blog/water-scarcity"];
  return (
    <SitePage path="blog/water-scarcity" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

    </SitePage>
  );
}
