import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";

export const metadata: Metadata = {
  title: "ماهواره — نمای کلی | اکو نوژین",
  description: "پایش ماهواره‌ای پوشش گیاهی و رطوبت.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["modules/satellite/overview"];
  return (
    <SitePage path="modules/satellite/overview" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

    </SitePage>
  );
}
