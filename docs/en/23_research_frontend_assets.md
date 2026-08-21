# 23. Design & Data Resources Research — Animations, Animated Emojis, Dashboards

**Date:** 2026-08-17 | **Status:** Approved | **Class:** Technical/Design

Research of four sources for the Eco Nojin frontend (dashboards, animations,
animated emojis): Dribbble (design inspiration), NASA GISS (free climate data),
Vercel (deployment + dashboard templates), LottieFiles (lightweight animations).

## 1) Dribbble — dribbble.com
- Largest UI/UX portfolio platform. Found: 177,000+ dashboard designs
  (`/tags/dashboard`), 27,074 dashboard-design, 22,064 dashboard-ui shots.
- Use: dashboard layout inspiration (KPI cards, charts, dark mode, RTL,
  data-viz); style reference for admin panel and science dashboard.
- Note: no downloadable files — inspiration only.

## 2) NASA GISS — data.giss.nasa.gov
- GISTEMP v4 surface temperature analysis (1880–present), updated ~10th monthly.
- Monthly time series (global/hemispheric/zonal), global anomaly/trend maps
  (`/gistemp/maps/`), downloadable text/CSV files.
- Use: free authoritative climate data for a climate-change dashboard;
  complements CMIP6/Copernicus already used by the project.

## 3) Vercel — vercel.com
- Serverless deployment platform optimized for Next.js (our frontend stack).
- Key features: automatic Preview Deployments per branch/PR, Web Analytics,
  v0 (AI UI generation), Edge Functions, AI streaming.
- **Next.js & shadcn/ui Admin Dashboard Template** with ready dashboards
  (Default, CRM, Finance, Analytics, Productivity) — aligns with the project's
  Radix/shadcn UI kit added in Phase 8.
- Use: preview/hosting option complementing the Docker/Nginx production plan.

## 4) LottieFiles — lottiefiles.com/featured-free-animations
- Largest Lottie animation library: 1.3M+ animations; free + premium.
- Formats: dotLottie, Lottie JSON (lightweight/vector/scalable), MP4, GIF.
  Official players: `lottie-web`, `@lottiefiles/react-lottie-player`.
- Relevant pages: `free-animations/dashboard`, `free-animations/dashboard-stats`,
  `free-animations/animated-emojis` (animated emojis — exactly what was asked).
- Alternatives: Lordicon, IconScout, useAnimations, Lottielab.
- Use: loading/empty/success animations, animated emojis in the RAG assistant,
  stats animations; Lottie JSON's tiny size matters for low-bandwidth /
  offline-first users.

## Recommendations
1. Dashboards: Dribbble inspiration + Vercel's shadcn/ui template (matches
   current Radix kit); charts via recharts (already integrated).
2. Animations: Lottie JSON + react-lottie-player; respect
   `prefers-reduced-motion` (already present).
3. Animated emojis: LottieFiles animated-emojis collection for chat/assistant.
4. Climate data: NASA GISS as a free complementary source (with attribution)
   alongside CMIP6/Copernicus.
5. Deployment: Vercel for previews/testing; Docker/Nginx for production
   (final decision with project owner).

## Sources (searched this turn)
- https://dribbble.com/tags/dashboard | /tags/dashboard-design | /tags/dashboard-ui
- https://data.giss.nasa.gov/gistemp/ | /gistemp/maps/
- https://climatedataguide.ucar.edu/climate-data/global-surface-temperature-data-gistemp-nasa-goddard-institute-space-studies-giss
- https://svs.gsfc.nasa.gov/5603/
- https://vercel.com/docs/frameworks/full-stack/nextjs | https://vercel.com/docs/analytics
- https://vercel.com/templates/next.js/next-js-and-shadcn-ui-admin-dashboard
- https://lottiefiles.com/free-animations/dashboard | /dashboard-stats | /animated-emojis | https://lottiefiles.com/
- https://miromiro.app/blog/free-lottie-animations-best-resources
