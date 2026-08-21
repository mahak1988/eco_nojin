import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";
import FarmDashboard from "@/components/site/FarmDashboard";

export const metadata: Metadata = {
  title: "مزرعه‌های من | اکو نوژین",
  description: "فهرست مزرعه‌های ثبت‌شده و وضعیت هر کدام.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["dashboard/farms"];
  return (
    <SitePage path="dashboard/farms" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

      <FarmDashboard />
    </SitePage>
  );
}
