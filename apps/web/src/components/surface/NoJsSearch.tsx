import { getTranslations } from 'next-intl/server';

/**
 * A search form that works with JavaScript disabled.
 *
 * The master plan requires every content page to stay reachable without a
 * script (`§8`, "sustained degradation without JS for content pages"), and a
 * server-rendered `<form method="get">` is the whole implementation: submitting
 * it navigates to the same URL with `?q=…`, the page reads the term from
 * `searchParams`, and the server re-renders the results. Nothing depends on a
 * bundle having loaded.
 *
 * It is a *server* component that resolves its own copy rather than taking it
 * as props. A form whose labels are injected means every caller has to remember
 * four strings, and a caller that forgets renders an unlabelled input in twelve
 * locales — which is worse than having no form, because it looks finished. The
 * copy lives once, in `search.*`, and a page that mounts this cannot ship
 * without it.
 *
 * The previous version of this file also carried an inline `style` prop with
 * physical `marginBlockStart`-adjacent declarations; the layout is Tailwind
 * logical utilities now, so it mirrors correctly under RTL without a
 * `:dir(rtl)` rule.
 *
 * ## Two kinds, one form
 *
 * `kind="search"` is a term. `kind="value"` is an identifier the contract
 * requires — a wallet address, a user id. Both are the same problem at the
 * transport level: a GET that cannot answer a bare request, so the reader has to
 * supply something before there is anything to show. Two contracts on the
 * gateway are of the second kind and were rendering a permanent error state:
 * `GET /api/v1/carbon/credits/balance` requires `address`, and
 * `GET /api/v1/auth/profile/public` requires `user_id`.
 *
 * The value kind is labelled from itself — the parameter name and the contract
 * path, both language-neutral and both already on the page — rather than from a
 * translated sentence. That is not a compromise on the fourteen-locale
 * requirement; it is the same promise the contract line below the form makes,
 * and a parameter named `address` needs no translation to be understood.
 */
export type NoJsSearchKind = 'search' | 'value';

export interface NoJsSearchProps {
  /** The `name` of the input, which is also the query parameter. */
  name: string;
  /** The contract path shown beneath the form, so a reader can ask the same question. */
  path: string;
  /** The currently applied term, echoed back so the field is not empty on reload. */
  value?: string;
  /** Shown under the field when a search returned nothing. */
  emptyResult?: string;
  /** `search` for a term, `value` for an identifier the contract requires. */
  kind?: NoJsSearchKind;
  id: string;
}

export async function NoJsSearch({
  name,
  path,
  value = '',
  emptyResult,
  kind = 'search',
  id,
}: NoJsSearchProps) {
  const t = await getTranslations('search');
  const isSearch = kind === 'search';

  return (
    // No `role="search"` here. The element is a real `<form>` with a
    // `type="search"` field, which the browser already exposes correctly; adding
    // the role back is what Biome's `useSemanticElements` rejects, and an earlier
    // revision of this file carried it for the same reason it was removed the
    // first time. A `<search>` wrapper element would be the alternative, but it is
    // newer than the oldest browsers this platform still supports offline, and
    // shipping a11y that breaks on those is not an improvement.
    <form method="get" action="" className="mt-6">
      <label htmlFor={id} className="block text-sm font-medium text-ink">
        {isSearch ? t('label') : <span className="num">{name}</span>}
      </label>
      {/*
        Required only for the value kind, and only because the gateway returns
        422 without it. On the search kind the page has a real first render — the
        list — so requiring the field would block the reader from seeing anything.
      */}
      <div className="mt-2 flex flex-wrap gap-2">
        <input
          id={id}
          type={isSearch ? 'search' : 'text'}
          name={name}
          defaultValue={value}
          required={!isSearch}
          placeholder={isSearch ? t('placeholder') : name}
          className="min-h-11 min-w-0 flex-1 rounded-md border border-line bg-surface px-3 py-2 text-ink"
        />
        {/*
          `--action` / `--on-action`, not `bg-forest` / `text-on-action`. The
          latter measures 18.07:1 in light mode but 4.31:1 in dark, where
          `--forest` is the light branch — the same mistake the primary button
          variant was making, and invisible until the contrast gate measured it.
          `check-contrast.mjs` now holds this pair.
        */}
        <button type="submit" className="min-h-11 rounded-md bg-action px-4 py-2 text-on-action">
          {isSearch ? t('submit') : name}
        </button>
      </div>
      {/*
        The contract is printed rather than implied, so a reader can repeat the
        question from a terminal or a script — which is the same promise the
        provenance stamp makes about the data below it.
      */}
      <p className="num mt-2 break-all text-xs text-ink-faint">{path}</p>
      {emptyResult ? (
        <p role="status" className="mt-2 text-sm text-ink-soft">
          {emptyResult}
        </p>
      ) : null}
    </form>
  );
}

export default NoJsSearch;
