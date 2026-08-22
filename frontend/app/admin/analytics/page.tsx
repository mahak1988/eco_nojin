"use client";

import AdminNav from "@/components/site/AdminNav";
import AdminAnalytics from "@/components/site/AdminAnalytics";

export default function AdminPage() {
  return (
    <div className="space-y-4">
      <AdminNav />
      <AdminAnalytics />
    </div>
  );
}
