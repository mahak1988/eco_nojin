export interface SupportPersona {
  lang: string;
  name: string;
  role: string;
  intro: string;
  model: string;
}

export function SupportDirectory({
  personas,
  heading,
  headingId,
  unavailable,
  endpoint,
  endpointState,
}: {
  personas: readonly SupportPersona[];
  heading: string;
  headingId: string;
  unavailable: string;
  endpoint: string;
  endpointState: string;
}) {
  return (
    <section aria-labelledby={headingId}>
      <h2 id={headingId} className="field-label">
        {heading}
      </h2>
      <p className="num mt-2 text-xs text-ink-soft">
        <code>{endpoint}</code> · {endpointState}
      </p>
      {personas.length === 0 ? (
        <p className="mt-3 text-sm text-copper">{unavailable}</p>
      ) : (
        <ul className="mt-3 grid gap-3 sm:grid-cols-2">
          {personas.map((persona) => (
            <li key={`${persona.lang}:${persona.name}`} className="card p-4">
              <p className="text-sm font-semibold text-ink">{persona.name}</p>
              <p className="mt-1 text-xs text-ink-soft">{persona.intro}</p>
              <dl className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs">
                <div className="flex gap-2">
                  <dt className="num text-ink-faint">lang</dt>
                  <dd className="num text-ink-soft" lang={persona.lang}>
                    {persona.lang}
                  </dd>
                </div>
                <div className="flex gap-2">
                  <dt className="num text-ink-faint">role</dt>
                  <dd className="text-ink-soft">{persona.role}</dd>
                </div>
                <div className="flex gap-2">
                  <dt className="num text-ink-faint">model</dt>
                  <dd className="num text-ink-soft">{persona.model}</dd>
                </div>
              </dl>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
