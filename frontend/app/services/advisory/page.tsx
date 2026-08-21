import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";

export const metadata: Metadata = {
  title: "خدمت مشاوره علمی | اکو نوژین",
  description: "دستیار دانش‌بنیان کشاورزی: سؤال بپرسید، پاسخ مستند بگیرید.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["services/advisory"];
  return (
    <SitePage path="services/advisory" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

    </SitePage>
  );
}
