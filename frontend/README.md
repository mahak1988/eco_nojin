# 🌱 Eco Nojin Frontend

Monorepo for Eco Nojin scientific agricultural platform.

## Structure

```
frontend/
├── apps/
│   ├── web/          # 🌐 Eco NojiN (Public)
│   └── dashboard/    # 🎯 HyDroMa (Professional)
├── packages/
│   ├── ui/           # Design System
│   ├── api/          # Type-safe API Client
│   ├── models/       # Scientific Models SDK
│   ├── charts/       # Chart Components
│   ├── geo/          # GIS/Maps
│   ├── auth/         # Authentication
│   ├── i18n/         # Translations
│   ├── utils/        # Shared utilities
│   └── config/       # Shared configs
└── tooling/
    ├── typescript/   # TS configs
    ├── tailwind/     # Tailwind preset
    └── biome/        # Biome configs
```

## Development

```bash
# Install dependencies
pnpm install

# Start all apps
pnpm dev

# Start specific app
pnpm --filter @eco/web dev          # http://localhost:5173
pnpm --filter @eco/dashboard dev    # http://localhost:5174

# Build
pnpm build

# Test
pnpm test

# Lint
pnpm lint

# Type check
pnpm type-check
```

## Tech Stack

- React 18.3
- TypeScript 5.9 (strict)
- Vite 5 / 6
- Tailwind CSS v4
- TanStack Router + Query
- Zustand
- Turborepo + pnpm
- Biome (lint/format)

## Phase 1 — Foundation ✅

- [x] Monorepo + pnpm workspaces
- [x] Turborepo configuration
- [x] Strict TypeScript (with `noPropertyAccessFromIndexSignature`)
- [x] Biome linting
- [x] Two app shells (web + dashboard)
- [x] Nine package shells
- [x] Design tokens (colors, spacing, typography, shadows)
- [x] RTL-first (Persian + Arabic + Urdu + English)