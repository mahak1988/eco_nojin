import { columnsOf, formatCell, type ManualRecord, type ManualValue } from '@/lib/api/manual';

/**
 * Renders whatever the gateway actually sent, without asserting a shape.
 *
 * Most catalogue endpoints publish an empty or `additionalProperties: true`
 * response schema, so the frontend cannot type a field, a unit or a label
 * without inventing it. This view therefore reads the structure back from the
 * payload: a single object becomes a definition list, an array of objects
 * becomes a table whose header row is the dataset's own column names, and
 * anything else is shown as the plain value it is.
 *
 * The rule is narrow on purpose. A key that the server did not send produces no
 * row, a value that is absent produces an em dash, and nothing here is ever
 * labelled as verified.
 */

/** A payload the gateway may legitimately return for these routes. */
export type SurfaceValue = ManualValue | SurfaceValue[] | { [key: string]: SurfaceValue };

export function isPlainObject(value: unknown): value is ManualRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/** Object rows of an array payload; anything else yields no rows. */
export function objectRowsOf(value: SurfaceValue): ManualRecord[] {
  if (!Array.isArray(value)) return [];
  return value.filter(isPlainObject);
}

/**
 * Content-derived row keys.
 *
 * A gateway payload has no position field, so a key taken from the array index
 * would remount every cell whenever the dataset re-sorted. Each key is built
 * from the item's own rendered content, and identical items stay distinct
 * through a per-content occurrence counter.
 */
function keyedByContent<T>(items: readonly T[], contentOf: (item: T) => string): string[] {
  const seen = new Map<string, number>();
  return items.map((item) => {
    const base = contentOf(item);
    const count = seen.get(base) ?? 0;
    seen.set(base, count + 1);
    return count === 0 ? base : `${base}#${count}`;
  });
}

function scalarText(value: SurfaceValue): string {
  if (isPlainObject(value)) {
    return Object.entries(value)
      .map(([key, item]) => `${key}=${scalarText(item as SurfaceValue)}`)
      .join(' ');
  }
  if (Array.isArray(value)) return value.map(scalarText).join(' ');
  return formatCell(value as ManualValue);
}

function ScalarList({ values }: { values: SurfaceValue[] }) {
  const keys = keyedByContent(values, scalarText);
  return (
    <ul className="flex flex-wrap gap-2">
      {values.map((value, position) => (
        <li
          key={keys[position]}
          className="num rounded-md border border-line px-2 py-1 text-xs text-ink-soft"
        >
          {formatCell(value as ManualValue)}
        </li>
      ))}
    </ul>
  );
}

function Scalar({ value }: { value: SurfaceValue }) {
  if (Array.isArray(value)) {
    if (value.length === 0) return <span className="text-ink-faint">—</span>;
    if (value.every((item) => !isPlainObject(item) && !Array.isArray(item))) {
      return <ScalarList values={value} />;
    }
    return <NestedList values={value} />;
  }
  if (isPlainObject(value)) return <ObjectView record={value} />;
  return (
    <span className={typeof value === 'number' ? 'num' : undefined}>
      {formatCell(value as ManualValue)}
    </span>
  );
}

function NestedList({ values }: { values: SurfaceValue[] }) {
  const rows = objectRowsOf(values);
  if (rows.length > 0) {
    return <RecordTableView records={rows} caption={undefined} />;
  }
  const keys = keyedByContent(values, scalarText);
  return (
    <ul className="flex flex-col gap-1">
      {values.map((value, position) => (
        <li key={keys[position]} className="text-sm text-ink-soft">
          <Scalar value={value} />
        </li>
      ))}
    </ul>
  );
}

function ObjectView({ record }: { record: ManualRecord }) {
  const entries = Object.entries(record);
  if (entries.length === 0) return <span className="text-ink-faint">—</span>;
  return (
    <dl className="grid gap-3 sm:grid-cols-2">
      {entries.map(([key, value]) => (
        <div key={key}>
          <dt className="num text-xs text-ink-soft">{key}</dt>
          <dd className="mt-1 text-sm text-ink">
            <Scalar value={value as SurfaceValue} />
          </dd>
        </div>
      ))}
    </dl>
  );
}

function RecordTableView({ records, caption }: { records: ManualRecord[]; caption?: string }) {
  const columns = columnsOf(records);
  if (columns.length === 0) return null;
  const rowKeys = keyedByContent(records, (record) =>
    columns.map((column) => scalarText(record[column] as SurfaceValue)).join(' '),
  );
  return (
    <div className="mt-3 overflow-x-auto rounded-md border border-line">
      <table className="w-full border-collapse text-sm">
        {caption ? (
          <caption className="px-4 py-3 text-start text-xs text-ink-soft">{caption}</caption>
        ) : null}
        <thead>
          <tr className="border-b border-line">
            {columns.map((column) => (
              <th key={column} scope="col" className="px-4 py-2 text-start font-medium text-ink">
                <span className="num">{column}</span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {records.map((record, position) => (
            <tr key={rowKeys[position]} className="border-b border-line last:border-0">
              {columns.map((column) => (
                <td key={column} className="px-4 py-2 align-top text-ink-soft">
                  <Scalar value={record[column] as SurfaceValue} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Chooses the presentation from the payload rather than from a declared type.
 * A response of `{}` is a legitimate answer and renders as an empty object note.
 */
export function ShapeView({ value, caption }: { value: unknown; caption?: string }) {
  if (isPlainObject(value)) {
    const nested = value as ManualRecord;
    const rowsKey = ['data', 'results', 'items', 'rows', 'records', 'entries'].find((key) =>
      Array.isArray(nested[key]),
    );
    if (rowsKey) {
      return (
        <RecordTableView
          records={objectRowsOf(nested[rowsKey] as unknown as SurfaceValue)}
          caption={caption ?? rowsKey}
        />
      );
    }
    return <ObjectView record={nested} />;
  }
  if (Array.isArray(value)) {
    const rows = objectRowsOf(value as SurfaceValue[]);
    if (rows.length > 0) return <RecordTableView records={rows} caption={caption} />;
    if (value.length > 0) return <ScalarList values={value as SurfaceValue[]} />;
  }
  if (value === null || value === undefined) {
    return <p className="text-sm text-ink-soft">—</p>;
  }
  return <p className="text-sm text-ink">{formatCell(value as ManualValue)}</p>;
}
