import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";

export const metadata: Metadata = {
  title: "خدمت پایش مزرعه | اکو نوژین",
  description: "پایش ماهواره‌ای پوشش گیاهی، رطوبت و تنش — با داده واقعی از فاز ۴.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["services/monitoring"];
  return (
    <SitePage path="services/monitoring" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

    </SitePage>
  );
}
