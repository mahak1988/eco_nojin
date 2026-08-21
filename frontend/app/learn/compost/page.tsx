import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";
import Quiz from "@/components/site/Quiz";

export const metadata: Metadata = {
  title: "آموزش: کمپوست | اکو نوژین",
  description: "تولید کمپوست با کیفیت — از مواد اولیه تا محصول نهایی.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["learn/compost"];
  return (
    <SitePage path="learn/compost" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

      <Quiz category="compost" />
    </SitePage>
  );
}
