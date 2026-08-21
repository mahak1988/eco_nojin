import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";
import Quiz from "@/components/site/Quiz";

export const metadata: Metadata = {
  title: "آموزش: خاک | اکو نوژین",
  description: "مفاهیم پایه خاک — بافت، pH، ماده آلی، شوری و سلامت خاک.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["learn/soil"];
  return (
    <SitePage path="learn/soil" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

      <Quiz category="soil" />
    </SitePage>
  );
}
