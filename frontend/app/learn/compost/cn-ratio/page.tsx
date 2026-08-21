import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";

export const metadata: Metadata = {
  title: "مقاله: نسبت C/N کمپوست | اکو نوژین",
  description: "کلید موفقیت کمپوست: کربن و نیتروژن متعادل.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["learn/compost/cn-ratio"];
  return (
    <SitePage path="learn/compost/cn-ratio" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

    </SitePage>
  );
}
