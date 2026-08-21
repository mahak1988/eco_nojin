import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";

// recharts ResponsiveContainer needs measured dimensions; jsdom reports 0,
// so stub it with a fixed-size box that still renders the chart SVG.
vi.mock("recharts", async (importOriginal) => {
  const actual = await importOriginal<typeof import("recharts")>();
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => {
      const child = React.Children.only(children) as React.ReactElement<{ width?: number; height?: number }>;
      return (
        <div style={{ width: 400, height: 300 }}>
          {React.cloneElement(child, { width: 400, height: 300 })}
        </div>
      );
    },
  };
});

import * as React from "react";
import { Hydrograph } from "@/components/charts/hydrograph";
import { RainfallChart } from "@/components/charts/rainfall-chart";
import { SoilMoistureChart } from "@/components/charts/soil-moisture";
import { Et0Chart } from "@/components/charts/et0-chart";
import { FlowDurationCurve } from "@/components/charts/flow-duration";

describe("charts kit", () => {
  it("hydrograph renders svg", () => {
    const { container } = render(
      <Hydrograph data={[{ t: "00", q: 0.5 }, { t: "06", q: 2.1 }]} />
    );
    expect(container.querySelector("svg")).toBeTruthy();
  });

  it("rainfall renders", () => {
    const { container } = render(<RainfallChart data={[{ d: "شنبه", mm: 8 }]} />);
    expect(container.querySelector("svg")).toBeTruthy();
  });

  it("soil moisture renders", () => {
    const { container } = render(
      <SoilMoistureChart data={[{ t: "w1", theta: 0.28, fc: 0.35, pwp: 0.12 }]} />
    );
    expect(container.querySelector("svg")).toBeTruthy();
  });

  it("et0 renders", () => {
    const { container } = render(<Et0Chart data={[{ d: "خرداد", et0: 5.2 }]} />);
    expect(container.querySelector("svg")).toBeTruthy();
  });

  it("flow duration renders", () => {
    const { container } = render(
      <FlowDurationCurve data={[{ exceed: 5, q: 8 }, { exceed: 50, q: 1.2 }, { exceed: 95, q: 0.1 }]} />
    );
    expect(container.querySelector("svg")).toBeTruthy();
  });
});
