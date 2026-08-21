"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Label } from "@/components/ui/label";

/** FormField: برچسب + خطا + توضیح — wrapper روی react-hook-form */
interface FormFieldProps {
  label?: string;
  htmlFor?: string;
  required?: boolean;
  error?: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}

export function FormField({ label, htmlFor, required, error, description, children, className }: FormFieldProps) {
  return (
    <div className={cn("space-y-1.5", className)}>
      {label ? (
        <Label htmlFor={htmlFor}>
          {label}
          {required ? <span className="mr-1 text-destructive">*</span> : null}
        </Label>
      ) : null}
      {children}
      {description && !error ? (
        <p className="text-xs text-muted-foreground">{description}</p>
      ) : null}
      {error ? (
        <p role="alert" className="text-xs text-destructive">
          {error}
        </p>
      ) : null}
    </div>
  );
}

/** FormSection: گروه‌بندی بصری فرم */
export function FormSection({
  title,
  description,
  children,
  className,
}: {
  title?: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <fieldset className={cn("space-y-3 rounded-lg border p-4", className)}>
      {title ? <legend className="px-1 text-sm font-medium">{title}</legend> : null}
      {description ? <p className="text-xs text-muted-foreground">{description}</p> : null}
      {children}
    </fieldset>
  );
}
