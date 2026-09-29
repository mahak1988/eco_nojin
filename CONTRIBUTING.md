# Contributing to Hydroma Nojin

Thank you for contributing. This file defines how contributions are licensed
into the project and what is expected of you and of the maintainers.

## Licensing of contributions

By default, the repository is MIT-licensed (see [`LICENSE`](./LICENSE)). To keep
that unambiguous, every contribution is accepted under the **Hydroma Nojin
Contributor Licence Agreement (CLA)**, reproduced in full below.

You keep the copyright in your contribution. The CLA grants the project
permission to use and redistribute it as part of Hydroma Nojin under the same
MIT terms. It does **not** transfer ownership, it does not obligate you to
assign your copyright, and it does not affect your ability to use your own
contribution elsewhere.

### How to sign

Add one comment to your pull request using the exact text below. Do not edit it.

```text
Hydroma Nojin CLA v1 — Contributor Licence Agreement

I have read and agree to the terms of the Hydroma Nojin Contributor Licence
Agreement, and I certify that:

1. I am the sole author of the code and documentation I am contributing, or
   that I have the legal right to contribute it under these terms.
2. My contribution is original work, or is submitted under a licence
   compatible with the MIT licence that governs this project.
3. I have read the project's CODE_OF_CONDUCT and agree to follow it.

Contributor: <your name>
GitHub username: <your username>
Date: <YYYY-MM-DD>
```

A maintainer will confirm the sign-off. **An unsigned contribution cannot be
merged**, because the project cannot ship an MIT-licensed artefact that contains
work of unknown provenance. This is a licensing requirement, not a review
preference.

## Attribution

Contributors are recorded in `AUTHORS` and are recognised in the repository's
"All Contributors" listing. Add yourself when you open your first pull request.

## What we expect

### Code

- Match the surrounding style. The project uses `ruff` for formatting and
  linting, and `mypy` for type checking. Both run in pre-commit and in CI.
- Add or update tests. `pytest` is the runner; tests live in `tests/`.
- Do not add a dependency without explaining why in the pull request body. The
  project deliberately keeps its dependency surface small, for licensing and
  supply-chain reasons — see `reports/HYDROMA_NOJIN_ECONOMIC_EXECUTION_MODEL.md`.
- Contract changes under `contracts/` additionally require a written
  threat model and an invariant test. See `contracts/` for the state of that
  work, which is currently blocked: the Solidity sources have never compiled.

### Translation

The project ships 14 locales. **Do not machine-translate agronomy.** A
confidently wrong crop coefficient is worse than an English page, because a
farmer acts on it. Any change to `messages/*.json` must be reviewed by a
speaker of that language who knows the domain.

### Data and science

- Every number that reaches a user-facing surface must be traceable to a source
  or be explicitly labelled as a target or a scenario. See
  `reports/HYDROMA_NOJIN_CONSULTING_FRAMEWORK_FA.md` §0.2 for the four levels
  of claim and the wording rules.
- Never fabricate a placeholder, a stub value, or a hash. The project's
  credibility rests on the absence of fabricated data, which is worth more than
  any single feature.
- Model outputs must carry a version, a calibration set, and an uncertainty
  band. See `docs/` and `reports/OPEN_ITEMS_FA_2026-09-26.md`.

### Honest status

If a capability is not implemented, say so in the code and in the API response.
Do not report a feature as available when it is a stub. The
`/api/v1/blockchain/health` endpoint was corrected in September 2026 because
it reported seven capabilities as `True` while none were implemented; that
single line would have been visible to any funder or auditor who read the API
before the source.

## Security

Report a vulnerability through GitHub's private vulnerability reporting, not in
a public issue. See `SECURITY.md` once it exists — **it does not exist yet, and
creating it is an open item.**

## Code of Conduct

This project is committed to a respectful working environment. The maintainers
are establishing a `CODE_OF_CONDUCT.md`; until then, the GitHub Community
Guidelines apply.

## Licence

By contributing you agree that your contribution is licensed under the MIT
licence of this project, via the CLA above.
