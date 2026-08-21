import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";

export const metadata: Metadata = {
  title: "کشاورزی کربنی | اکو نوژین",
  description: "ترسیب کربن در خاک به‌عنوان راهکار اقلیمی و درآمد نو.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["blog/carbon-farming"];
  return (
    <SitePage path="blog/carbon-farming" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

    </SitePage>
  );
}
