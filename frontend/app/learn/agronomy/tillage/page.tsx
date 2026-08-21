import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";

export const metadata: Metadata = {
  title: "مقاله: خاک‌ورزی حفاظتی | اکو نوژین",
  description: "کم‌خاک‌ورزی و بی‌خاک‌ورزی.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["learn/agronomy/tillage"];
  return (
    <SitePage path="learn/agronomy/tillage" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

    </SitePage>
  );
}
