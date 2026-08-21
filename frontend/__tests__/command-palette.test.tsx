import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { I18nProvider } from "@/lib/i18n-context";
import { CommandPalette } from "@/components/site/CommandPalette";

const renderPalette = () =>
  render(
    <I18nProvider>
      <CommandPalette />
    </I18nProvider>
  );

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

describe("CommandPalette", () => {
  beforeEach(() => {
    push.mockClear();
  });

  it("opens with Ctrl+K and shows search input", () => {
    renderPalette();
    expect(screen.queryByPlaceholderText(/جستجوی صفحات/)).not.toBeInTheDocument();
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    expect(screen.getByPlaceholderText(/جستجوی صفحات/)).toBeInTheDocument();
  });

  it("navigates on item select", () => {
    renderPalette();
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    fireEvent.click(screen.getByText("خانه"));
    expect(push).toHaveBeenCalledWith("/");
  });
});
