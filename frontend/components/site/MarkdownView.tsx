"use client";

import { useMemo } from "react";

/** Escape HTML so user content can never inject markup. */
function esc(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function inline(text: string): string {
  return esc(text)
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(
      /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-primary underline">$1</a>',
    );
}

function renderMd(src: string): string {
  const lines = src.split("\n");
  const out: string[] = [];
  let list: string[] | null = null;
  let inCode = false;
  const flushList = () => {
    if (list) {
      out.push(`<ul class="list-disc space-y-1 pr-5">${list.map((li) => `<li>${li}</li>`).join("")}</ul>`);
      list = null;
    }
  };
  for (const raw of lines) {
    const line = raw.trimEnd();
    if (line.trim().startsWith("```")) {
      flushList();
      if (inCode) {
        out.push("</code></pre>");
        inCode = false;
      } else {
        out.push("<pre class=\"overflow-x-auto rounded-xl bg-muted p-3 text-xs leading-6\" dir=\"ltr\"><code>");
        inCode = true;
      }
      continue;
    }
    if (inCode) {
      out.push(esc(line));
      continue;
    }
    if (/^#{1,4}\s/.test(line)) {
      flushList();
      const level = line.match(/^(#{1,4})\s/)![1].length;
      out.push(`<h${level} class="mt-3 font-bold text-foreground">${inline(line.replace(/^#{1,4}\s/, ""))}</h${level}>`);
    } else if (/^\s*[-*]\s/.test(line)) {
      list = list ?? [];
      list.push(inline(line.replace(/^\s*[-*]\s/, "")));
    } else if (/^\d+\.\s/.test(line)) {
      flushList();
      out.push(`<p class="leading-7">${inline(line.replace(/^\d+\.\s/, ""))}</p>`);
    } else if (line.trim() === "") {
      flushList();
      out.push("<p class=\"h-2\"></p>");
    } else {
      flushList();
      out.push(`<p class="leading-7">${inline(line)}</p>`);
    }
  }
  flushList();
  if (inCode) out.push("</code></pre>");
  return out.join("\n");
}

/** Minimal safe Markdown renderer (no external deps, no raw HTML). */
export default function MarkdownView({ source, className }: { source: string; className?: string }) {
  const html = useMemo(() => renderMd(source), [source]);
  return (
    <div dir="rtl" className={`prose-sm max-w-none space-y-1 text-sm text-muted-foreground ${className ?? ""}`} dangerouslySetInnerHTML={{ __html: html }} />
  );
}
