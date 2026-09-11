import MiniChart from '../../components/dashboard/MiniChart';

export default {
  title: 'Dashboard/Calc Components',
  component: MiniChart,
  parameters: {
    layout: 'centered',
    docs: {
      story: {
        height: '400px',
      },
    },
  },
} as const;

export const FieldComponent = () => (
  <div className="mb-2 flex flex-col gap-1">
    <span className="text-[11px] font-bold text-[var(--color-night-200)]/65">
      Initial rate
      <span className="text-[var(--color-night-300)]/35">(mm/h)</span>
    </span>
    <input
      type="number"
      className="w-full rounded-lg border border-[var(--color-night-700)]/50 bg-[var(--color-night-900)]/80 px-3 py-1.5 text-xs text-[var(--color-night-100)] focus:border-[var(--color-leaf-400)]/60 focus:outline-none"
      defaultValue="130"
    />
  </div>
);
FieldComponent.storyName = 'Input Field';

export const ResultComponent = () => (
  <div className="glass rounded-xl px-3 py-2">
    <p className="text-[10px] text-[var(--color-night-200)]/45">6-hour cumulative</p>
    <p className="text-sm font-extrabold text-[var(--color-leaf-300)]" dir="ltr">
      330 <span className="text-[10px] font-bold text-[var(--color-night-200)]/45">mm</span>
    </p>
  </div>
);
ResultComponent.storyName = 'Result Display';

export const HubSubmitButton = () => (
  <div className="flex flex-col items-start gap-1.5">
    <button
      type="button"
      className="rounded-full bg-[var(--color-aqua-500)]/15 px-4 py-1.5 text-[11px] font-extrabold text-[var(--color-aqua-300)] transition-colors hover:bg-[var(--color-aqua-500)]/25 disabled:opacity-60"
    >
      Register in hub
    </button>
    <p className="text-[10px] font-bold text-[var(--color-leaf-300)]">Registered in the hub ✓</p>
  </div>
);
HubSubmitButton.storyName = 'Hub Submit Button';