import SitePage from "@/components/site/SitePage";
import Link from "next/link";
import { siteRegistry, SITE_GROUPS } from "@/lib/site-registry";

export default function PagesIndex() {
  return (
    <SitePage title="فهرست همه صفحات" description="دسترسی کامل به همه 170 صفحه فعال پلتفرم اکو نوژین." badge="نقشه سایت" related={["services", "learn", "tools", "science"]}>
      {SITE_GROUPS.map((group) => {
        const items = Object.values(siteRegistry).filter((e) => e.group === group.key);
        if (items.length === 0) return null;
        return (
          <section key={group.key} className="space-y-3">
            <h2 className="text-lg font-bold text-foreground">{group.title} ({items.length})</h2>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {items.map((e) => (
                <Link key={e.path} href={e.path} className="truncate rounded-lg border border-border px-3 py-2 text-sm text-foreground/80 transition-colors hover:border-primary hover:text-primary">
                  {e.title}
                </Link>
              ))}
            </div>
          </section>
        );
      })}
    </SitePage>
  );
}
