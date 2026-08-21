import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";

export const metadata: Metadata = {
  title: "همکاری با ما | اکو نوژین",
  description: "اکو نوژین با کار تیمی بدون نیروی فنی تمام‌وقت ساخته می‌شود — مشارکت موضوعی و میدانی بپذیریم.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["careers"];
  return (
    <SitePage path="careers" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

    </SitePage>
  );
}
