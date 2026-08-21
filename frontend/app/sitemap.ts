import type { MetadataRoute } from "next";
import { siteRegistry } from "@/lib/site-registry";

const BASE = process.env.NEXT_PUBLIC_SITE_URL || "https://eco-nojin.ir";

export default function sitemap(): MetadataRoute.Sitemap {
  return Object.values(siteRegistry).map((e) => ({
    url: `${BASE}${e.path === "/" ? "/" : `/${e.path}`}`,
    lastModified: new Date(),
    changeFrequency: "monthly",
    priority: e.path === "/" ? 1 : 0.7,
  }));
}
