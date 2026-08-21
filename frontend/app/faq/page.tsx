import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";
import FaqList from "@/components/site/FaqList";

export const metadata: Metadata = {
  title: "پرسش‌های پرتکرار | اکو نوژین",
  description: "پاسخ به پرسش‌های رایج درباره پلتفرم.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["faq"];
  return (
    <SitePage path="faq" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

      <FaqList />
    </SitePage>
  );
}
