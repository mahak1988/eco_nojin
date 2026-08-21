import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Sheet, SheetTrigger, SheetContent, SheetTitle } from "@/components/ui/sheet";

describe("Sheet", () => {
  it("opens and shows content", () => {
    render(
      <Sheet>
        <SheetTrigger>باز کن</SheetTrigger>
        <SheetContent>
          <SheetTitle>عنوان کشو</SheetTitle>
          <p>محتوای کشو</p>
        </SheetContent>
      </Sheet>
    );
    expect(screen.queryByText("محتوای کشو")).not.toBeInTheDocument();
    fireEvent.click(screen.getByText("باز کن"));
    expect(screen.getByText("محتوای کشو")).toBeInTheDocument();
  });

  it("closes via close button", () => {
    render(
      <Sheet defaultOpen>
        <SheetContent>
          <SheetTitle>عنوان کشو</SheetTitle>
          <p>محتوای کشو</p>
        </SheetContent>
      </Sheet>
    );
    fireEvent.click(screen.getByLabelText("بستن"));
    expect(screen.queryByText("محتوای کشو")).not.toBeInTheDocument();
  });
});
