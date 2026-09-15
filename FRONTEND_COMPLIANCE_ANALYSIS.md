# Frontend Compliance Analysis: Eco Nojin

**Report Date**: 12 September 2026  
**Analysis Date**: 12 September 2026  
**Project**: Eco Nojin (HyDroMa)  
**Frontend Stack**: React 18 + Vite 5 + TypeScript 5.9 + Tailwind CSS 4

---

## Executive Summary

The current frontend implementation provides a **strong foundation** with excellent architecture, bilingual content management, accessibility support, and visual design. However, **significant gaps exist** in performance-critical areas (SSR, PWA, real-time data, interactive maps/charts) that prevent the project from meeting the report's specifications and competing with market leaders.

**Overall Compliance Score**: **~65%** (Matches report's 7.5/10 overall rating)

---

## Detailed Comparison Matrix

| Area | Report Specification | Current Implementation | Status | Gap Severity |
|------|---------------------|------------------------|--------|--------------|
| **Architecture** | Component-based, Content/View separation, TypeScript strict | ✅ Implemented | ✅ Compliant | None |
| **SSR/SSG** | **Required** (Astro/Next.js migration) | ❌ Pure SPA (Vite) | ❌ Missing | 🔴 Critical |
| **PWA/Service Worker** | **Required** (Workbox, offline support) | ❌ Content claims PWA, no implementation | ❌ Missing | 🔴 Critical |
| **Interactive Maps** | MapLibre/deck.gl with real NDVI layers | ⚠️ SVG conceptual mock only | ❌ Missing | 🔴 Critical |
| **Real-time Data** | WebSocket/SSE for live counters | ❌ Mock/static data only | ❌ Missing | 🔴 Critical |
| **Interactive Charts** | Recharts/Chart.js/D3 | ⚠️ Custom SVG static charts | ⚠️ Partial | 🟡 Medium |
| **Skip Navigation** | Required for WCAG AA | ✅ **Exists** in Navbar (lines 51-56) | ✅ Compliant | Report error |
| **Global Search** | Required | ❌ Missing | ❌ Missing | 🟡 Medium |
| **Empty States** | Designed empty states | ⚠️ Component exists, underused | ⚠️ Partial | 🟡 Medium |
| **Skeleton Consistency** | Standardized skeleton | ✅ Skeleton component exists | ✅ Compliant | Minor usage gaps |
| **Code Consistency** | No inline styles, token usage | ❌ 15+ inline styles, hardcoded values | ❌ Non-compliant | 🟡 Medium |
| **Context Duplication** | Single dashboard context | ❌ DashboardCustomization + useDashboardOrder duplicate | ❌ Non-compliant | 🟡 Medium |
| **Bundle Analysis** | Visualizer script | ⚠️ Plugin configured, no script | ⚠️ Partial | 🟢 Low |
| **Print Stylesheet** | Required for reports | ❌ Missing | ❌ Missing | 🟢 Low |
| **TOC (Table of Contents)** | Required for long pages | ❌ Missing | ❌ Missing | 🟢 Low |
| **Onboarding Flow** | Interactive guide for new users | ❌ Missing | ❌ Missing | 🟢 Low |
| **Image Optimization** | WebP/AVIF, lazy loading | ❌ No optimization pipeline | ❌ Missing | 🟡 Medium |
| **Critical CSS** | Above-the-fold inlining | ❌ Missing | ❌ Missing | 🟡 Medium |
| **Environment Validation** | VITE_API_BASE_URL validation | ❌ Missing | ❌ Missing | 🟢 Low |

---

## Critical Findings

### 1. **SSR/SSG Missing (Highest Impact)**
- **Report**: "Migration to SSR/SSG for SEO and initial load speed (biggest impact)"
- **Current**: Pure SPA with Vite
- **Impact**: Poor SEO, slower initial load, no social sharing previews
- **Recommendation**: Migrate to **Astro** (preferred for content sites) or Next.js

### 2. **No Real PWA Implementation**
- **Report**: "Service Worker with Workbox for offline capability"
- **Current**: Content *claims* PWA support in 5+ places but **zero implementation**
- **Impact**: False advertising, no offline support, fails Lighthouse PWA audit

### 3. **Satellite Map is Conceptual Only**
- **Report**: "Replace conceptual SVG with real MapLibre + NDVI layers"
- **Current**: `SatelliteMap.tsx` uses hardcoded radial gradients, static markers
- **Impact**: Core differentiator (satellite monitoring) is not functional

### 4. **No Real-time Data Pipeline**
- **Report**: "WebSocket/SSE for live counter updates"
- **Current**: All data static/mock, `LiveCounters` component shows countdown only
- **Impact**: Dashboard shows stale data, no live monitoring capability

### 5. **Duplicate Dashboard State Management**
- **Report**: "Merge `DashboardCustomization` and `useDashboardOrder`"
- **Current**: Two separate implementations with identical `DEFAULT_ORDER` and localStorage keys
- **Impact**: Inconsistent state, double persistence, maintenance burden

---

## Implementation Plan

### Phase 1: Critical Infrastructure (Weeks 1-4) 🔴

#### 1.1 Migrate to Astro for SSR/SSG
- **Why Astro**: Island Architecture perfect for content-heavy site, React components work natively
- **Steps**:
  1. Initialize Astro project with React integration
  2. Migrate pages to `.astro` files with React islands for interactive components
  3. Configure SSR adapter (Node.js or edge)
  4. Set up sitemap generation, RSS feeds
  5. Implement `getStaticPaths` for content pages
- **Effort**: 2-3 weeks
- **Dependencies**: None (can start immediately)

#### 1.2 Implement PWA with Workbox
- **Steps**:
  1. Add `@vite-pwa/workbox` or `vite-plugin-pwa`
  2. Configure `manifest.webmanifest` (icons, shortcuts, display: standalone)
  3. Implement Service Worker with:
     - Cache-first for static assets
     - Network-first for API calls
     - Offline fallback page
  4. Add install prompt UI
  5. Test offline functionality
- **Effort**: 1 week
- **Dependencies**: Can parallelize with 1.1

#### 1.3 Replace SatelliteMap with MapLibre GL
- **Steps**:
  1. Add `maplibre-gl` dependency
  2. Create `InteractiveSatelliteMap` component with:
     - MapLibre GL JS initialization
     - Vector tile source for NDVI (Sentinel Hub / custom tiles)
     - Project markers with popups
     - Layer controls (NDVI, NDWI, True Color)
  3. Integrate with Sentinel Hub API for real tiles
  4. Add loading states and error handling
  5. Fallback to conceptual SVG for unsupported browsers
- **Effort**: 2 weeks
- **Dependencies**: Requires backend tile service or Sentinel Hub integration

#### 1.4 Real-time Data Pipeline (WebSocket/SSE)
- **Steps**:
  1. Design WebSocket protocol for metric updates
  2. Create `useRealtimeMetrics` hook with reconnection logic
  3. Implement SSE fallback for broader compatibility
  4. Update `LiveCounters` to consume live data
  5. Add connection status indicator
- **Effort**: 1-2 weeks
- **Dependencies**: Backend WebSocket/SSE endpoint

---

### Phase 2: UX & Code Quality (Weeks 5-8) 🟡

#### 2.1 Consolidate Dashboard Contexts
- **Steps**:
  1. Merge `DashboardCustomization` + `useDashboardOrder` into single `DashboardContext`
  2. Single localStorage key, unified API
  3. Add TypeScript types for section visibility + order
  4. Migrate all dashboard components
- **Effort**: 3 days

#### 2.2 Create `useBilingual()` Helper Hook
- **Steps**:
  1. Extract `lang === 'fa'` checks into `useBilingual()` hook
  2. Returns `{ t: content[lang], lang, isRTL }`
  3. Replace 30+ occurrences across components
  4. Add TypeScript inference for content keys
- **Effort**: 2 days

#### 2.3 Eliminate Inline Styles & Hardcoded Values
- **Steps**:
  1. Audit all `style={{}}` usages (15+ components)
  2. Convert to Tailwind v4 `@theme` tokens or CSS custom properties
  3. Add missing tokens to `index.css` `@theme` block
  4. Configure `tailwindcss` to use CSS variables
- **Effort**: 1 week

#### 2.4 Standardize Loading/Empty States
- **Steps**:
  1. Audit all pages for loading patterns
  2. Enforce `Skeleton` component usage (remove ad-hoc spinners)
  3. Apply `EmptyState` component to Hub, Dashboard, Search results
  4. Add empty state variants (no data, no results, error, offline)
- **Effort**: 3 days

#### 2.5 Implement Global Search
- **Steps**:
  1. Add `fuse.js` or `minisearch` for client-side search
  2. Build search index from content files at build time
  3. Create `SearchModal` component (Cmd+K / Ctrl+K)
  4. Add debounced search API endpoint for server-side search
  5. Keyboard navigation (arrow keys, Enter, Escape)
- **Effort**: 1 week

#### 2.6 Add Bundle Analysis Script
- **Steps**:
  1. Add `rollup-plugin-visualizer` to devDependencies
  2. Add `build:analyze` script to package.json
  3. Configure output to `dist/stats.html`
  4. Integrate into CI for PR size tracking
- **Effort**: 2 hours

---

### Phase 3: Enhanced Features (Weeks 9-14) 🟡

#### 3.1 Interactive Charts with Recharts
- **Steps**:
  1. Add `recharts` dependency
  2. Replace custom SVG charts in:
     - `ImpactTimeSeries` → `LineChart` with tooltip, zoom
     - `NdviConceptChart` → `AreaChart` with real data
     - Dashboard calculators → responsive charts
  3. Add chart themes matching design system
  4. Implement responsive containers
- **Effort**: 1 week

#### 3.2 Print Stylesheet for Reports
- **Steps**:
  1. Create `print.css` with `@media print`
  2. Hide navigation, footers, backgrounds
  3. Optimize typography for print
  4. Add page breaks for report sections
  5. Test PDF generation from browser
- **Effort**: 2 days

#### 3.3 Table of Contents for Long Pages
- **Steps**:
  1. Create `useTableOfContents` hook (scans `h2`, `h3`)
  2. Build `TableOfContents` component with scroll spy
  3. Add to Impact, Dashboard, Carbon pages
  4. Collapsible on mobile
- **Effort**: 3 days

#### 3.4 Image Optimization Pipeline
- **Steps**:
  1. Add `@vite-plugin-imagemin` or Sharp-based pipeline
  2. Convert all images to WebP/AVIF at build
  3. Implement responsive images with `picture` element
  4. Add blur-up placeholders
- **Effort**: 3 days

#### 3.5 Critical CSS Inlining
- **Steps**:
  1. Add `vite-plugin-critical` or `critters`
  2. Configure for above-the-fold content
  3. Test LCP improvement
- **Effort**: 2 days

#### 3.6 Environment Validation
- **Steps**:
  1. Add `zod` schema for `import.meta.env`
  2. Validate at app startup
  3. Fail fast with clear error messages
- **Effort**: 2 hours

---

### Phase 4: Strategic Modernization (Months 4-6) 🟢

#### 4.1 React 19 Migration
- **Steps**:
  1. Upgrade to React 19 RC
  2. Enable Server Components (requires SSR framework)
  3. Replace `useEffect` data fetching with `use()` hook
  4. Implement streaming SSR with Suspense boundaries
- **Effort**: 2 weeks (depends on Phase 1.1)

#### 4.2 AI Advisory Engine (Frontend)
- **Steps**:
  1. Design chat interface component
  2. Integrate with backend AI API
  3. Add streaming responses
  4. Context-aware suggestions based on dashboard data
- **Effort**: 3 weeks

#### 4.3 Mobile App Preparation (React Native)
- **Steps**:
  1. Extract shared logic to `@eco/shared` package
  2. Set up React Native Web + Expo
  3. Identify platform-specific components
  4. Plan code sharing strategy
- **Effort**: 2 weeks planning

---

### Phase 5: Long-term Vision (Months 6-12) 🔵

#### 5.1 API Marketplace Frontend
- Developer portal, API docs, key management, usage analytics

#### 5.2 Digital Twin Integration
- 3D visualization with Three.js / React Three Fiber
- CesiumJS for geospatial digital twins

#### 5.3 Carbon Marketplace UI
- Trading interface, portfolio management, MRV verification views

#### 5.4 ReFi Protocol Dashboard
- DeFi integration, staking, governance UI

---

## Resource Requirements

| Phase | Frontend Devs | Backend Devs | DevOps | Designer | QA |
|-------|---------------|--------------|--------|----------|-----|
| Phase 1 | 2 | 1 (WS/SSE) | 1 (Astro deploy) | 0.5 | 0.5 |
| Phase 2 | 1 | 0 | 0 | 0.5 | 0.5 |
| Phase 3 | 1 | 0 | 0 | 0.5 | 0.5 |
| Phase 4 | 2 | 1 (AI API) | 0.5 | 1 | 1 |
| Phase 5 | 2+ | 2+ | 1 | 1 | 1 |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Astro migration breaks React components | Medium | High | Incremental migration, island architecture |
| MapLibre tile service unavailable | High | High | Prepare fallback, negotiate Sentinel Hub access |
| WebSocket backend not ready | Medium | High | SSE fallback, mock server for development |
| PWA cache invalidation issues | Medium | Medium | Versioned cache names, clear update strategy |
| Bundle size increases with new deps | Medium | Medium | Bundle budgets, treeshaking, code splitting |

---

## Success Metrics

| Metric | Current | Target (Phase 1) | Target (Phase 3) |
|--------|---------|------------------|------------------|
| Lighthouse Performance | ~55 | >85 | >90 |
| Lighthouse Accessibility | ~90 | >95 | >98 |
| Lighthouse SEO | ~60 | >90 | >95 |
| Lighthouse PWA | 0 | >90 | >95 |
| First Contentful Paint | ~2.5s | <1.2s | <0.8s |
| Time to Interactive | ~4s | <2.5s | <1.5s |
| Bundle Size (gzipped) | ~180KB | <150KB | <120KB |
| Real-time Data Latency | N/A | <500ms | <200ms |

---

## Immediate Next Steps

1. **Week 1**: Start Astro migration spike (proof of concept with 3 pages)
2. **Week 1**: Add Workbox PWA plugin configuration
3. **Week 1**: Begin MapLibre integration research (tile sources, licensing)
4. **Week 2**: Consolidate Dashboard contexts (quick win)
5. **Week 2**: Create `useBilingual()` hook (quick win)
6. **Week 2**: Add bundle analysis script (quick win)

---

## Appendix: Report Discrepancies

The report claims **Skip Navigation Link is missing** (Section 3.2.a), but it **exists** in `Navbar.tsx:51-56`:

```tsx
<a
  href="#main-content"
  className="sr-only focus:not-sr-only ..."
>
  {lang === 'fa' ? 'پرش به محتوای اصلی' : 'Skip to main content'}
</a>
```

This should be corrected in future report versions.