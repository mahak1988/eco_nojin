"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Mail } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const KEY = "eco-nojin-newsletter";

export default function NewsletterForm() {
  const [email, setEmail] = useState("");

  const submit = () => {
    const value = email.trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
      toast.error("ایمیل معتبر وارد کنید.");
      return;
    }
    try {
      const existing = JSON.parse(localStorage.getItem(KEY) ?? "[]") as string[];
      if (!existing.includes(value)) {
        existing.push(value);
        localStorage.setItem(KEY, JSON.stringify(existing));
      }
    } catch {
      /* storage blocked */
    }
    setEmail("");
    toast.success("عضویت شما در خبرنامه ثبت شد 🌱");
  };

  return (
    <div className="flex flex-col gap-3 sm:flex-row">
      <Input
        type="email"
        dir="ltr"
        placeholder="you@example.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && submit()}
      />
      <Button onClick={submit} className="shrink-0">
        <Mail className="h-4 w-4" />
        عضویت در خبرنامه
      </Button>
    </div>
  );
}
