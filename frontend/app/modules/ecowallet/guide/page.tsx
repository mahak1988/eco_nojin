import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import { pageContent } from "@/lib/site-content";

export const metadata: Metadata = {
  title: "کیف پول اکو — راهنما | اکو نوژین",
  description: "راهنمای گام‌به‌گام استفاده از ماژول کیف پول اکو.",
  openGraph: { title: "اکو نوژین", description: "پلتفرم دانش‌بنیان کشاورزی اقلیم‌هوشمند، آب، خاک و کربن" },
};

export default function Page() {
  const c = pageContent["modules/ecowallet/guide"];
  return (
    <SitePage path="modules/ecowallet/guide" title={c.title} description={c.description} badge={c.badge} sections={c.sections} related={c.related}>

    </SitePage>
  );
}
