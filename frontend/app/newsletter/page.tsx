import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";
import NewsletterForm from "@/components/site/NewsletterForm";

export const metadata: Metadata = {
  title: "خبرنامه | اکو نوژین",
  description: "خلاصه هفتگی اخبار علمی و به‌روزرسانی‌های پلتفرم.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["newsletter"];
  return (
    <SitePage path="newsletter" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

      <NewsletterForm />
    </SitePage>
  );
}
