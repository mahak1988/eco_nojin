# syntax=docker/dockerfile:1.7
# Eco Nojin frontend (apps/web) — multi-stage Next.js production image.
#
# The build context MUST be the monorepo root because @eco/web resolves its
# workspace dependencies (@eco/ui, @eco/api-client, @eco/types) through pnpm:
#
#   docker build -f apps/web/Dockerfile -t ghcr.io/eco-nojin/frontend:latest .
#   docker build -f apps/web/Dockerfile \
#     --build-arg NEXT_PUBLIC_SITE_URL=https://staging-app.eco-nojin.org \
#     -t ghcr.io/eco-nojin/frontend:staging-latest .
#
# Runtime contract (mirrored in k8s/base/frontend-deployment.yaml):
#   - runs as the unprivileged "node" user (uid/gid 1000)
#   - serves HTTP on 0.0.0.0:3000
#   - /health is the liveness/startup probe, /ready the readiness probe
#   - writable paths only: apps/web/.next/cache and /tmp
#
# apps/web/next.config.ts does not set `output: "standalone"`, so the runtime
# serves the prebuilt output with `next start` (the same entry point CI e2e uses)
# on a production-only dependency tree. Adding `output: "standalone"` to the
# Next config later needs no change here and only shrinks the image.

ARG NODE_VERSION=22
ARG PNPM_VERSION=11.4.0
ARG NEXT_DIST_DIR=.next
ARG NEXT_PUBLIC_SITE_URL=https://app.eco-nojin.org

FROM node:${NODE_VERSION}-bookworm-slim AS base
ENV PNPM_HOME=/pnpm \
    PATH=/pnpm:$PATH \
    CI=true \
    NEXT_TELEMETRY_DISABLED=1

FROM base AS pnpm-base
ARG PNPM_VERSION
RUN corepack disable > /dev/null 2>&1 || true; \
    npm install --global "pnpm@${PNPM_VERSION}"; \
    pnpm --version

FROM pnpm-base AS deps
WORKDIR /app
COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages/api-client/package.json ./packages/api-client/package.json
COPY packages/types/package.json ./packages/types/package.json
COPY packages/ui/package.json ./packages/ui/package.json
RUN --mount=type=cache,id=eco-nojin-pnpm-store,target=/pnpm/store \
    pnpm install --store-dir=/pnpm/store --frozen-lockfile --filter "@eco/web..." && \
    set -- node_modules/.pnpm/typescript@*/node_modules/typescript && \
    cp -r "$1" /tmp/runtime-typescript

FROM deps AS builder
ARG NEXT_DIST_DIR
ARG NEXT_PUBLIC_SITE_URL
ENV NEXT_DIST_DIR=${NEXT_DIST_DIR} \
    NEXT_PUBLIC_SITE_URL=${NEXT_PUBLIC_SITE_URL}
COPY apps/web/src ./apps/web/src
COPY apps/web/public ./apps/web/public
COPY apps/web/messages ./apps/web/messages
COPY apps/web/tokens ./apps/web/tokens
COPY apps/web/next.config.ts ./apps/web/next.config.ts
COPY apps/web/tsconfig.json ./apps/web/tsconfig.json
COPY apps/web/postcss.config.mjs ./apps/web/postcss.config.mjs
COPY apps/web/tailwind.config.ts ./apps/web/tailwind.config.ts
COPY packages/api-client/src ./packages/api-client/src
COPY packages/types/src ./packages/types/src
COPY packages/ui/src ./packages/ui/src
RUN pnpm -C apps/web build

FROM pnpm-base AS prod-deps
WORKDIR /app
COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages/api-client/package.json ./packages/api-client/package.json
COPY packages/types/package.json ./packages/types/package.json
COPY packages/ui/package.json ./packages/ui/package.json
RUN --mount=type=cache,id=eco-nojin-pnpm-store,target=/pnpm/store \
    pnpm install --store-dir=/pnpm/store --frozen-lockfile --prod --filter "@eco/web..."

FROM base AS runner
ARG NEXT_DIST_DIR
ENV NEXT_DIST_DIR=${NEXT_DIST_DIR} \
    NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0
WORKDIR /app
COPY --from=prod-deps --chown=node:node /app/node_modules ./node_modules
COPY --from=prod-deps --chown=node:node /app/apps/web/node_modules ./apps/web/node_modules
COPY --from=prod-deps --chown=node:node /app/packages/api-client/node_modules ./packages/api-client/node_modules
COPY --from=prod-deps --chown=node:node /app/packages/types/node_modules ./packages/types/node_modules
COPY --from=prod-deps --chown=node:node /app/packages/ui/node_modules ./packages/ui/node_modules
# next start transpiles next.config.ts through the TypeScript API at boot; keep it
# resolvable from the app directory so no runtime install is attempted.
COPY --from=deps --chown=node:node /tmp/runtime-typescript ./node_modules/typescript
COPY --from=builder --chown=node:node /app/apps/web/package.json ./apps/web/package.json
COPY --from=builder --chown=node:node /app/apps/web/next.config.ts ./apps/web/next.config.ts
COPY --from=builder --chown=node:node /app/apps/web/tsconfig.json ./apps/web/tsconfig.json
COPY --from=builder --chown=node:node /app/apps/web/messages ./apps/web/messages
COPY --from=builder --chown=node:node /app/apps/web/public ./apps/web/public
COPY --from=builder --chown=node:node /app/apps/web/${NEXT_DIST_DIR} ./apps/web/${NEXT_DIST_DIR}
COPY --from=builder --chown=node:node /app/packages/api-client/package.json ./packages/api-client/package.json
COPY --from=builder --chown=node:node /app/packages/api-client/src ./packages/api-client/src
COPY --from=builder --chown=node:node /app/packages/types/package.json ./packages/types/package.json
COPY --from=builder --chown=node:node /app/packages/types/src ./packages/types/src
COPY --from=builder --chown=node:node /app/packages/ui/package.json ./packages/ui/package.json
COPY --from=builder --chown=node:node /app/packages/ui/src ./packages/ui/src
RUN mkdir -p "/app/apps/web/${NEXT_DIST_DIR}/cache" /tmp && \
    chown -R node:node "/app/apps/web/${NEXT_DIST_DIR}/cache" /tmp
WORKDIR /app/apps/web
USER node
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD node -e "fetch('http://127.0.0.1:3000/health').then((r) => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"
CMD ["node_modules/.bin/next", "start", "-p", "3000", "-H", "0.0.0.0"]
