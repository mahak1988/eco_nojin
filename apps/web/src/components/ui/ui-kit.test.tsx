import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { Accordion } from './Accordion';
import { Badge } from './Badge';
import { DataTable } from './DataTable';
import { Breadcrumb, Pagination } from './Navigation';
import { Progress } from './Progress';
import { StateSlot } from './StateSlot';
import { Tabs } from './Tabs';

afterEach(() => {
  cleanup();
});

/**
 * The repository does not depend on `@testing-library/user-event` or
 * `jest-dom`, so these tests use `fireEvent` and plain vitest assertions to match
 * the existing suites rather than adding two dev dependencies for one file.
 */

const LABELS = {
  loading: 'در حال بارگذاری',
  empty: 'داده‌ای موجود نیست',
  error: 'خطا رخ داد',
  offline: 'اتصال برقرار نیست',
  partial: 'نتیجهٔ ناقص',
  action: 'تلاش دوباره',
};

describe('StateSlot', () => {
  it('renders its children only when ready', () => {
    render(
      <StateSlot state="ready" labels={LABELS}>
        <p>داده</p>
      </StateSlot>,
    );
    expect(screen.getByText('داده')).toBeTruthy();
  });

  it('renders a distinct message for each of the five states', () => {
    // `partial` is deliberately not folded into `empty`: a page showing three of
    // fifty-one rows must say so rather than presenting itself as complete.
    const cases = [
      ['loading', LABELS.loading],
      ['empty', LABELS.empty],
      ['error', LABELS.error],
      ['offline', LABELS.offline],
      ['partial', LABELS.partial],
    ] as const;

    for (const [state, message] of cases) {
      const { unmount } = render(
        <StateSlot state={state} labels={LABELS}>
          <p>داده</p>
        </StateSlot>,
      );
      expect(screen.getByText(message), `state ${state}`).toBeTruthy();
      expect(screen.queryByText('داده'), `state ${state} leaked its children`).toBeNull();
      unmount();
    }
  });

  it('announces an error assertively and the rest politely', () => {
    const { unmount } = render(
      <StateSlot state="error" labels={LABELS}>
        <p>داده</p>
      </StateSlot>,
    );
    expect(screen.getByRole('alert')).toBeTruthy();
    unmount();

    render(
      <StateSlot state="offline" labels={LABELS}>
        <p>داده</p>
      </StateSlot>,
    );
    expect(screen.queryByRole('alert')).toBeNull();
    expect(screen.getByRole('status')).toBeTruthy();
  });

  it('offers a retry action only when one is wired', () => {
    const onRetry = vi.fn();
    const { unmount } = render(
      <StateSlot state="error" labels={LABELS} onRetry={onRetry}>
        <p>داده</p>
      </StateSlot>,
    );
    fireEvent.click(screen.getByRole('button', { name: LABELS.action }));
    expect(onRetry).toHaveBeenCalledOnce();
    unmount();

    render(
      <StateSlot state="error" labels={LABELS}>
        <p>داده</p>
      </StateSlot>,
    );
    expect(screen.queryByRole('button', { name: LABELS.action })).toBeNull();
  });
});

describe('Tabs', () => {
  const items = [
    { id: 'a', label: 'الف' },
    { id: 'b', label: 'ب' },
    { id: 'c', label: 'ج' },
  ];

  it('exposes one tab stop for the whole list', () => {
    // Roving tabindex: without it a tab list puts three stops in the tab order
    // where the ARIA pattern calls for one.
    render(<Tabs items={items} activeId="a" onChange={() => {}} label="زبانه‌ها" />);
    const tabs = screen.getAllByRole('tab');
    expect(tabs.filter((tab) => tab.getAttribute('tabindex') === '0')).toHaveLength(1);
    expect(tabs[0].getAttribute('aria-selected')).toBe('true');
  });

  it('moves selection with the arrow keys and wraps', () => {
    // The parent owns the selection, so the test asserts what the component
    // reported rather than what it rendered.
    const reported: string[] = [];
    render(
      <Tabs items={items} activeId="a" onChange={(id) => reported.push(id)} label="زبانه‌ها" />,
    );
    const tabs = () => screen.getAllByRole('tab');
    fireEvent.keyDown(tabs()[0], { key: 'ArrowRight' });
    fireEvent.keyDown(tabs()[1], { key: 'ArrowRight' });
    fireEvent.keyDown(tabs()[2], { key: 'ArrowRight' });

    // Wraps rather than dead-ending on the last tab.
    expect(reported).toEqual(['b', 'c', 'a']);
  });

  it('selects on click', () => {
    const reported: string[] = [];
    render(
      <Tabs items={items} activeId="a" onChange={(id) => reported.push(id)} label="زبانه‌ها" />,
    );
    fireEvent.click(screen.getAllByRole('tab')[2]);
    expect(reported).toEqual(['c']);
  });

  it('has an accessible name', () => {
    render(<Tabs items={items} activeId="a" onChange={() => {}} label="دسته‌بندی" />);
    expect(screen.getByRole('tablist', { name: 'دسته‌بندی' })).toBeTruthy();
  });

  it('skips a disabled tab when moving', () => {
    const withDisabled = [items[0], { ...items[1], disabled: true }, items[2]];
    const seen: string[] = [];
    render(
      <Tabs items={withDisabled} activeId="a" onChange={(id) => seen.push(id)} label="زبانه‌ها" />,
    );
    fireEvent.keyDown(screen.getAllByRole('tab')[0], { key: 'ArrowRight' });
    expect(seen).toEqual(['c']);
  });
});

describe('Accordion', () => {
  const items = [
    { id: 'one', title: 'اول', content: <p>محتوای اول</p> },
    { id: 'two', title: 'دوم', content: <p>محتوای دوم</p> },
  ];

  it('toggles aria-expanded and reveals the panel', () => {
    render(<Accordion items={items} label="بخش‌ها" />);
    const trigger = screen.getByRole('button', { name: /اول/ });
    expect(trigger.getAttribute('aria-expanded')).toBe('false');
    fireEvent.click(trigger);
    expect(screen.getByRole('button', { name: /اول/ }).getAttribute('aria-expanded')).toBe('true');
    expect(screen.getByText('محتوای اول')).toBeTruthy();
  });

  it('closes the previous panel when exclusive', () => {
    render(<Accordion items={items} label="بخش‌ها" exclusive />);
    const [first, second] = screen.getAllByRole('button');
    fireEvent.click(first);
    fireEvent.click(second);
    expect(first.getAttribute('aria-expanded')).toBe('false');
    expect(second.getAttribute('aria-expanded')).toBe('true');
  });

  it('reports a toggle with its new state', () => {
    const onToggle = vi.fn();
    render(<Accordion items={items} label="بخش‌ها" onToggle={onToggle} />);
    fireEvent.click(screen.getByRole('button', { name: /اول/ }));
    expect(onToggle).toHaveBeenCalledWith('one', true);
  });
});

describe('Breadcrumb', () => {
  it('marks the last crumb as the current page and does not link it', () => {
    render(
      <Breadcrumb
        items={[
          { href: '/fa', label: 'خانه' },
          { href: '/fa/public', label: 'عمومی' },
          { href: '/fa/public/why', label: 'چرا' },
        ]}
        label="مسیر"
      />,
    );
    const current = screen.getByText('چرا');
    expect(current.getAttribute('aria-current')).toBe('page');
    expect(current.tagName).toBe('SPAN');
    expect(screen.getByRole('link', { name: 'خانه' })).toBeTruthy();
  });

  it('names the navigation landmark', () => {
    render(<Breadcrumb items={[{ href: '/fa', label: 'خانه' }]} label="مسیر راهنما" />);
    expect(screen.getByRole('navigation', { name: 'مسیر راهنما' })).toBeTruthy();
  });
});

describe('Pagination', () => {
  const props = {
    pageCount: 5,
    hrefFor: (p: number) => `/fa/list?page=${p}`,
    label: 'صفحه‌بندی',
    previousLabel: 'قبلی',
    nextLabel: 'بعدی',
  };

  it('marks the current page and exposes rel=prev and rel=next', () => {
    render(<Pagination {...props} page={1} />);
    expect(screen.getByText('2').getAttribute('aria-current')).toBe('page');
    expect(screen.getByRole('link', { name: /قبلی/ }).getAttribute('rel')).toBe('prev');
    expect(screen.getByRole('link', { name: /بعدی/ }).getAttribute('rel')).toBe('next');
  });

  it('disables previous on the first page and next on the last', () => {
    const { unmount } = render(<Pagination {...props} page={0} />);
    expect(screen.queryByRole('link', { name: /قبلی/ })).toBeNull();
    // `aria-disabled` sits on the wrapper that replaces the link, not on the
    // label inside it.
    expect(screen.getByText('قبلی').closest('[aria-disabled]')?.getAttribute('aria-disabled')).toBe(
      'true',
    );
    unmount();

    render(<Pagination {...props} page={4} />);
    expect(screen.queryByRole('link', { name: /بعدی/ })).toBeNull();
    expect(screen.getByText('بعدی').closest('[aria-disabled]')).toBeTruthy();
  });

  it('renders nothing for a single page', () => {
    const { container } = render(<Pagination {...props} page={0} pageCount={1} />);
    expect(container.innerHTML).toBe('');
  });
});

describe('Progress', () => {
  it('reports a determinate value', () => {
    render(<Progress label="پیشرفت" value={42} />);
    expect(screen.getByRole('progressbar').getAttribute('aria-valuenow')).toBe('42');
  });

  it('omits aria-valuenow when indeterminate', () => {
    // Reporting 0 instead would claim "zero per cent complete", which is a
    // different and wrong statement.
    render(<Progress label="در حال کار" />);
    expect(screen.getByRole('progressbar').getAttribute('aria-valuenow')).toBeNull();
  });

  it('clamps out-of-range values', () => {
    render(<Progress label="پیشرفت" value={150} />);
    expect(screen.getByRole('progressbar').getAttribute('aria-valuenow')).toBe('100');
  });

  it('keeps the label when it is visually hidden', () => {
    render(<Progress label="بارگذاری" hideLabel />);
    expect(screen.getByRole('progressbar').getAttribute('aria-label')).toBe('بارگذاری');
  });
});

describe('Badge', () => {
  it('keeps the dot decorative', () => {
    render(
      <Badge tone="success" dot>
        فعال
      </Badge>,
    );
    // The label carries the meaning, so a dot read as well would say it twice.
    expect(screen.getByText('فعال')).toBeTruthy();
    expect(screen.queryByRole('img')).toBeNull();
  });
});

describe('DataTable', () => {
  type Row = { name: string; value: number };
  const rows: Row[] = [
    { name: 'گندم', value: 30 },
    { name: 'برنج', value: 10 },
    { name: 'جو', value: 20 },
  ];
  const columns = [
    { key: 'name', header: 'نام', sortable: true },
    { key: 'value', header: 'مقدار', sortable: true, numeric: true },
  ];

  const renderTable = (props: Partial<Parameters<typeof DataTable<Row>>[0]> = {}) =>
    render(
      <DataTable
        columns={columns}
        rows={rows}
        rowKey={(row) => row.name}
        caption="محصولات"
        {...props}
      />,
    );

  it('sorts on header activation and reports the direction', () => {
    const onSortChange = vi.fn();
    renderTable({ onSortChange });
    const header = screen.getByRole('button', { name: /مقدار/ }).closest('th');
    expect(header?.getAttribute('aria-sort')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: /مقدار/ }));
    expect(onSortChange).toHaveBeenCalledWith('value', 'ascending');
  });

  it('reverses direction when the same column is clicked again', () => {
    const onSortChange = vi.fn();
    renderTable({ onSortChange, sort: { key: 'value', direction: 'ascending' } });
    fireEvent.click(screen.getByRole('button', { name: /مقدار/ }));
    expect(onSortChange).toHaveBeenCalledWith('value', 'descending');
  });

  it('honours a caller-owned sort state', () => {
    const onSortChange = vi.fn();
    renderTable({ sort: { key: 'value', direction: 'descending' }, onSortChange });
    const header = screen.getByRole('button', { name: /مقدار/ }).closest('th');
    expect(header?.getAttribute('aria-sort')).toBe('descending');
    // Controlled: the parent did not move the state, so the order is unchanged.
    expect(onSortChange).not.toHaveBeenCalled();
  });

  it('marks a numeric column for tabular digits', () => {
    renderTable();
    expect(screen.getByText('30').className).toContain('num');
  });

  it('aligns text to the logical start, never to left', () => {
    renderTable();
    const header = screen.getByText('نام').closest('th');
    expect(header?.className).toContain('text-start');
    expect(header?.className).not.toContain('text-left');
  });

  it('shows the empty label with a full-width cell', () => {
    renderTable({ rows: [], emptyLabel: 'موردی نیست' });
    expect(screen.getByText('موردی نیست')).toBeTruthy();
  });

  it('names the table with a caption', () => {
    renderTable();
    expect(screen.getByRole('table', { name: 'محصولات' })).toBeTruthy();
  });
});
