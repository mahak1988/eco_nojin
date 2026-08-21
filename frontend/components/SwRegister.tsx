"use client";

import { useEffect } from "react";
import { registerServiceWorker } from "@/lib/swRegistration";

/**
 * Registers the PWA service worker once, in production only.
 * Development keeps hot reload free of SW caching surprises.
 */
export default function SwRegister() {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production") return;
    registerServiceWorker().catch((err) => {
      console.warn("[SW] registration failed:", err);
    });
  }, []);
  return null;
}
