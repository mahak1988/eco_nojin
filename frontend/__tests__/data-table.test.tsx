import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DataTable, type Column } from "@/components/ui/data-table";

interface Row {
  name: string;
  area: number;
}

const columns: Column<Row>[] = [
  { key: "name", header: "نام", searchable: true, sortable: true },
  { key: "area", header: "مساحت", sortable: true },
];

const rows: Row[] = [
  { name: "مزرعه الف", area: 4 },
  { name: "مزرعه ب", area: 12 },
  { name: "مزرعه ج", area: 7 },
];

describe("DataTable", () => {
  it("renders rows and headers", () => {
    render(<DataTable<Row> columns={columns} rows={rows} responsive={false} />);
    expect(screen.getByText("نام")).toBeInTheDocument();
    expect(screen.getByText("مزرعه الف")).toBeInTheDocument();
    expect(screen.getByText("مزرعه ج")).toBeInTheDocument();
  });

  it("filters by search query", () => {
    render(<DataTable<Row> columns={columns} rows={rows} responsive={false} />);
    fireEvent.change(screen.getByLabelText("جستجو"), { target: { value: "ب" } });
    expect(screen.getByText("مزرعه ب")).toBeInTheDocument();
    expect(screen.queryByText("مزرعه الف")).not.toBeInTheDocument();
  });

  it("shows empty state when no match", () => {
    render(<DataTable<Row> columns={columns} rows={rows} responsive={false} />);
    fireEvent.change(screen.getByLabelText("جستجو"), { target: { value: "zzz" } });
    expect(screen.getByText("داده‌ای یافت نشد")).toBeInTheDocument();
  });

  it("paginates with pageSize=2", () => {
    render(<DataTable<Row> columns={columns} rows={rows} pageSize={2} responsive={false} />);
    expect(screen.getByText("مزرعه الف")).toBeInTheDocument();
    expect(screen.queryByText("مزرعه ج")).not.toBeInTheDocument();
    fireEvent.click(screen.getByText("بعدی"));
    expect(screen.getByText("مزرعه ج")).toBeInTheDocument();
  });

  it("sorts by column", () => {
    render(<DataTable<Row> columns={columns} rows={rows} responsive={false} />);
    fireEvent.click(screen.getByText("مساحت"));
    const cells = screen.getAllByText(/مزرعه/);
    expect(cells[0].textContent).toBe("مزرعه ب");
  });

  it("shows loading skeleton", () => {
    render(<DataTable<Row> columns={columns} rows={rows} loading responsive={false} />);
    expect(screen.getByTestId("data-table-loading")).toBeInTheDocument();
  });
});
