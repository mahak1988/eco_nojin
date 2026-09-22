# Frontend API Type Generation Guide

This document explains how to generate TypeScript types from the OpenAPI schema and keep them in sync with the backend API.

## Overview

The frontend uses `openapi-typescript` to generate type-safe TypeScript types from the backend's OpenAPI 3.1 schema (`openapi_schema.json`). This ensures that API calls are fully typed and catches breaking changes at compile time.

## Files

| File | Purpose |
|------|---------|
| `openapi_schema.json` | Backend OpenAPI 3.1 schema (source of truth) |
| `apps/web/src/lib/api/types.ts` | Generated TypeScript types (DO NOT EDIT MANUALLY) |
| `apps/web/src/lib/api/client.ts` | Typed API client wrapper |
| `apps/web/src/lib/auth/local.ts` | Auth functions using typed client |

## Regeneration Commands

### Local Development

```bash
# From repo root
pnpm -C apps/web generate:api

# Or from apps/web directory
cd apps/web && pnpm generate:api
```

This runs:
```bash
openapi-typescript ../../openapi_schema.json -o src/lib/api/types.ts
```

### CI/CD

The GitHub Actions workflow (`.github/workflows/ci.yml`) includes a `generate-api` job that runs on every push/PR:

```yaml
generate-api:
  name: Generate API Types
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: pnpm/action-setup@v4
      with:
        version: 11.4.0
    - uses: actions/setup-node@v4
      with:
        node-version: 22
        cache: pnpm
    - run: pnpm install --frozen-lockfile
    - run: pnpm -C apps/web generate:api
```

The `lint`, `type-check`, and `i18n-check` jobs depend on `generate-api`, ensuring types are always up-to-date before other checks run.

## Updating the OpenAPI Schema

When backend API changes are made:

1. **Backend**: Regenerate `openapi_schema.json` by running the backend's schema generation script
2. **Frontend**: Run `pnpm -C apps/web generate:api` to update types
3. **Verify**: Run `pnpm -C apps/web type-check` to catch any breaking changes
4. **Commit**: Commit both the updated schema and generated types together

## Using Generated Types

### In Auth Functions

```typescript
// apps/web/src/lib/auth/local.ts
import { authApi, type AuthSession, type UserProfile } from '@/lib/api/client';

export async function login(input: { email: string; password: string }): Promise<AuthSession> {
  const response = await authApi.login(input);
  return toSession(response, 'local');
}
```

### In React Hooks

```typescript
// apps/web/src/lib/auth/useAuth.ts
import { useMutation } from '@tanstack/react-query';
import * as localAuth from '@/lib/auth/local';
import type { components } from '@/lib/api/types';

type LoginInput = components['schemas']['services__api_gateway__routers__auth__LoginRequest'];

// Frontend-friendly register input (camelCase)
export interface RegisterInput {
  email: string;
  password: string;
  fullName: string;
  role: 'farmer' | 'researcher' | 'organization' | 'tourist' | 'regular';
  language: 'fa' | 'en' | 'ar' | 'tr';
  // ...
}
```

### Direct API Calls

```typescript
import { typedApiRequest } from '@/lib/api/client';

// Type-safe API call with path parameters
const landscape = await typedApiRequest(
  '/api/v1/platform/landscapes/{id}',
  'get',
  { pathParams: { id: '123' } }
);
```

## Type Mapping

| Backend (snake_case) | Frontend (camelCase) | Conversion |
|---------------------|---------------------|------------|
| `full_name` | `fullName` | In `local.ts` register function |
| `accept_tos` | `acceptTos` | In `local.ts` register function |
| `accept_privacy` | `acceptPrivacy` | In `local.ts` register function |
| `refresh_token` | `refreshToken` | In `local.ts` refresh function |

The `local.ts` module handles conversion between frontend camelCase and backend snake_case.

## Troubleshooting

### Type Errors After Schema Update

If `pnpm type-check` fails after regenerating types:

1. Check the error message for missing/changed fields
2. Update `local.ts` conversion functions if field names changed
3. Update Zod schemas in `apps/web/src/app/[locale]/auth/register/page.tsx` if validation rules changed
4. Update `useAuth.ts` `RegisterInput` interface if new fields added

### Missing Schemas

If a schema referenced in `client.ts` doesn't exist in the generated types:

1. Verify the endpoint exists in the OpenAPI schema
2. Check the schema name in `components['schemas']`
3. Some endpoints may return inline types (not named schemas) - use `unknown` for those

### Complex Type Errors

The `typedApiRequest` generic function can produce complex union types. If you see "Expression produces a union type that is too complex to represent":

- Use explicit type arguments: `typedApiRequest<ExpectedResponse>('/path', 'get')`
- Or use the simpler `apiGet`/`apiPost` helpers in `client.ts`

## Best Practices

1. **Never edit `types.ts` manually** - always regenerate
2. **Commit schema + types together** - they must be in sync
3. **Use frontend-friendly types in hooks** - convert in `local.ts`
4. **Run type-check before committing** - catches breaking changes early
5. **Keep Zod schemas in sync** - validation should match API contract

## Related Files

- `apps/web/package.json` - `generate:api` script
- `apps/web/src/lib/api/client.ts` - Typed API client
- `apps/web/src/lib/auth/local.ts` - Auth API functions
- `apps/web/src/lib/auth/useAuth.ts` - Auth React hooks
- `.github/workflows/ci.yml` - CI pipeline with type generation