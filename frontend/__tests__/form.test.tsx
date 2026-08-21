import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { FormField, FormSection } from "@/components/ui/form";

describe("FormField", () => {
  it("renders label, required mark and error", () => {
    render(
      <FormField label="مساحت" required error="مقدار الزامی است">
        <input />
      </FormField>
    );
    expect(screen.getByText("مساحت")).toBeInTheDocument();
    expect(screen.getByText("*")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("مقدار الزامی است");
  });

  it("shows description when no error", () => {
    render(
      <FormField label="بارش" description="میلی‌متر">
        <input />
      </FormField>
    );
    expect(screen.getByText("میلی‌متر")).toBeInTheDocument();
  });
});

describe("FormSection", () => {
  it("renders legend", () => {
    render(<FormSection title="مشخصات خاک">محتوا</FormSection>);
    expect(screen.getByText("مشخصات خاک")).toBeInTheDocument();
  });
});
