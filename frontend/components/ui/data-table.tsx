"use client";

import * as React from "react";
import { ArrowUpDown, ChevronDown, Download, Search } from "lucide-react";

import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
  sortable?: boolean;
  searchable?: boolean;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  loading?: boolean;
  pageSize?: number;
  emptyMessage?: string;
  /** در موبایل به کارت تبدیل می‌شود (به جای جدول) */
  responsive?: boolean;
  className?: string;
  /** ستون‌هایی که در نمای کارت موبایل نمایش داده می‌شوند (پیش‌فرض: همه) */
  cardKeys?: string[];
}

function valueOf<T>(row: T, key: string): string {
  const v = (row as Record<string, unknown>)[key];
  if (v === null || v === undefined) return "";
  return String(v);
}

/** DataTable عمومی: جستجو + مرتب‌سازی + صفحه‌بندی + خروجی CSV */
export function DataTable<T extends object>({
  columns,
  rows,
  loading = false,
  pageSize = 10,
  emptyMessage = "داده‌ای یافت نشد",
  responsive = true,
  className,
  cardKeys,
}: DataTableProps<T>) {
  const [query, setQuery] = React.useState("");
  const [sortKey, setSortKey] = React.useState<string | null>(null);
  const [sortDir, setSortDir] = React.useState<"asc" | "desc">("asc");
  const [page, setPage] = React.useState(0);

  const filtered = React.useMemo(() => {
    const q = query.trim().toLowerCase();
    let out = rows;
    if (q) {
      const searchable = columns.filter((c) => c.searchable !== false);
      out = rows.filter((r) =>
        searchable.some((c) => valueOf(r, c.key).toLowerCase().includes(q))
      );
    }
    if (sortKey) {
      out = [...out].sort((a, b) => {
        const av = valueOf(a, sortKey);
        const bv = valueOf(b, sortKey);
        const cmp = av.localeCompare(bv, "fa");
        return sortDir === "asc" ? cmp : -cmp;
      });
    }
    return out;
  }, [rows, query, sortKey, sortDir, columns]);

  const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const safePage = Math.min(page, pages - 1);
  const slice = filtered.slice(safePage * pageSize, (safePage + 1) * pageSize);

  const toggleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const exportCsv = () => {
    const header = columns.map((c) => c.header).join(",");
    const body = rows
      .map((r) => columns.map((c) => `"${valueOf(r, c.key).replace(/"/g, '""')}"`).join(","))
      .join("\n");
    const blob = new Blob(["\ufeff" + header + "\n" + body], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "export.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className={cn("w-full space-y-3", className)}>
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[180px]">
          <Search className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(0);
            }}
            placeholder="جستجو…"
            className="pr-9"
            aria-label="جستجو"
          />
        </div>
        <Button variant="outline" size="sm" onClick={exportCsv}>
          <Download className="h-3.5 w-3.5" />
          خروجی CSV
        </Button>
      </div>

      {loading ? (
        <div className="space-y-2" data-testid="data-table-loading">
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-9 w-full" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
          {emptyMessage}
        </div>
      ) : (
        <>
          {/* Desktop: جدول */}
          <div className="hidden overflow-x-auto rounded-lg border md:block">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  {columns.map((c) => (
                    <th key={c.key} className="px-3 py-2 text-right font-medium text-muted-foreground">
                      {c.sortable ? (
                        <button
                          type="button"
                          className="inline-flex items-center gap-1 hover:text-foreground"
                          onClick={() => toggleSort(c.key)}
                        >
                          {c.header}
                          <ArrowUpDown className="h-3 w-3" />
                        </button>
                      ) : (
                        c.header
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {slice.map((r, i) => (
                  <tr key={i} className="border-b last:border-0 hover:bg-muted/30">
                    {columns.map((c) => (
                      <td key={c.key} className="px-3 py-2">
                        {c.render ? c.render(r) : valueOf(r, c.key)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile: کارت */}
          {responsive && (
            <div className="grid gap-2 md:hidden">
              {slice.map((r, i) => (
                <div key={i} className="rounded-lg border p-3">
                  {(cardKeys ?? columns.map((c) => c.key)).map((k) => {
                    const col = columns.find((c) => c.key === k);
                    if (!col) return null;
                    return (
                      <div key={k} className="flex items-center justify-between gap-2 py-0.5 text-sm">
                        <span className="text-muted-foreground">{col.header}</span>
                        <span className="font-medium">
                          {col.render ? col.render(r) : valueOf(r, k)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {pages > 1 && (
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>
                صفحه {safePage + 1} از {pages}
              </span>
              <div className="flex gap-1">
                <Button variant="outline" size="sm" disabled={safePage === 0} onClick={() => setPage(safePage - 1)}>
                  قبلی
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={safePage >= pages - 1}
                  onClick={() => setPage(safePage + 1)}
                >
                  بعدی
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
