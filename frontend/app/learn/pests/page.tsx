import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";
import Quiz from "@/components/site/Quiz";

export const metadata: Metadata = {
  title: "آموزش: آفات | اکو نوژین",
  description: "مدیریت تلفیقی آفات (IPM) و کنترل زیستی.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["learn/pests"];
  return (
    <SitePage path="learn/pests" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

      <Quiz category="pests" />
    </SitePage>
  );
}
