import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";

export const metadata: Metadata = {
  title: "همکاری دانشگاهی | اکو نوژین",
  description: "برنامه پایلوت میدانی با دانشگاه‌ها — سه روستا (فاز ۱۰).",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["news/partnership"];
  return (
    <SitePage path="news/partnership" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

    </SitePage>
  );
}
