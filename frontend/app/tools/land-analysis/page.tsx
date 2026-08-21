import type { Metadata } from "next";
import SitePage from "@/components/site/SitePage";
import PlatformAnalysisPanel from "@/components/site/PlatformAnalysisPanel";

export const metadata: Metadata = {
  title: "تحلیل جامع زمین | اکو نوجین",
  description:
    "تحلیل علمی چندلایه زمین با دادههای ERA5 مدل RUSLE شاخص NDVI و ارزشگذاری اعتبار کربن.",
  openGraph: {
    title: "تحلیل جامع زمین | اکو نوجین",
    description:
      "پلتفرم تحلیل سرزمین با دادههای ماهوارهای اقلیمی و مدلهای شتابیافته C++.",
  },
};

export default function Page() {
  return (
    <SitePage
      path="tools/land-analysis"
      title="تحلیل جامع زمین"
      description="تحلیل علمی چندلایه با دادههای ERA5 مدل RUSLE شاخص NDVI و ارزشگذاری اعتبار کربن"
      badge="تحلیل پلتفرم"
      related={["tools", "tools/erosion", "tools/carbon-stock", "learn/soil", "learn/climate"]}
    >
      <PlatformAnalysisPanel />
    </SitePage>
  );
}
