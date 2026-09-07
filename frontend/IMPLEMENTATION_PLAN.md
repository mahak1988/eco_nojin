# Comprehensive Implementation Plan — Missing UI/UX Components

> Target: `@eco/ui` package within `D:\eco_nojin\frontend\packages\ui\`
> Stack: React 18, TypeScript, Tailwind CSS 4, Radix UI primitives

---

## 1. Advanced Animations

### 1.1 Lottie Integration
**Technical Approach:**
- Use `lottie-web` for web, `@lottiefiles/react-lottie-player` for React wrapper
- Create `<LottiePlayer>` primitive that accepts `animationData`, `loop`, `autoplay`, `speed`
- Add `LottieIcon` variant for inline icon animations

**Libraries:** `lottie-web`, `@lottiefiles/react-lottie-player`
**Files:** `src/primitives/lottie-player.tsx`, `src/primitives/lottie-icon.tsx`

### 1.2 Spring Physics Animations
**Technical Approach:**
- Implement `useSpring` hook using `requestAnimationFrame` with spring physics formula
- Tension/friction model: `x += (target - x) * tension; vx += (target - x) * tension - vx * friction`
- Create `<SpringMotion>` primitive for declarative spring animations

**Libraries:** None (custom implementation)
**Files:** `src/primitives/spring-motion.tsx`, `src/hooks/useSpring.ts`

### 1.3 Parallax Effects
**Technical Approach:**
- Use `IntersectionObserver` + scroll event listeners with throttling
- Create `<ParallaxSection>` composite with `speed` prop (0-1)
- Implement transform-based parallax for performance (GPU accelerated)

**Libraries:** None (custom implementation)
**Files:** `src/composites/parallax-section.tsx`, `src/hooks/useParallax.ts`

### 1.4 Staggered Animations
**Technical Approach:**
- Extend existing `animate-fade-up` with `animation-delay` based on index
- Create `<StaggerContainer>` composite that wraps children
- Support `staggerDelay` prop (default: 70ms)

**Libraries:** None (CSS-based)
**Files:** `src/composites/stagger-container.tsx`

### 1.5 Shared Element Transitions
**Technical Approach:**
- Use `FLIP` animation technique (First, Last, Invert, Play)
- Create `<SharedElement>` context provider
- Implement `useSharedElement()` hook for registering elements
- Use `getBoundingClientRect()` for position calculation

**Libraries:** None (custom implementation with `framer-motion` as optional)
**Files:** `src/composites/shared-element-transition.tsx`, `src/hooks/useSharedElement.ts`

---

## 2. Specialized Widgets

### 2.1 Stopwatch
**Technical Approach:**
- `useStopwatch` hook with `start`, `stop`, `reset`, `lap` methods
- Render laps list with `AnimatedCounter` for milliseconds
- Use `requestAnimationFrame` for precision

**Files:** `src/primitives/stopwatch.tsx`, `src/hooks/useStopwatch.ts`

### 2.2 Weather/Clock/Stock Ticker
**Technical Approach:**
- **Clock:** 12/24h toggle, analog + digital modes, timezone support
- **Weather:** Mock data adapter (real API integration later), icon-based conditions
- **Stock Ticker:** Horizontal scroll with `overflow-x-auto`, real-time update simulation

**Files:** `src/primitives/clock.tsx`, `src/primitives/weather-widget.tsx`, `src/primitives/stock-ticker.tsx`

### 2.3 QR/Barcode Scanner
**Technical Approach:**
- Use `@zxing/browser` or `html5-qrcode` for camera access
- Create `<Scanner>` primitive with `onScan` callback
- Fallback to file upload if camera unavailable

**Libraries:** `@zxing/browser` or `html5-qrcode`
**Files:** `src/primitives/qr-scanner.tsx`

### 2.4 Signature Pad
**Technical Approach:**
- Canvas-based drawing with `pointerdown/move/up` events
- Export as PNG/SVG via `canvas.toDataURL()`
- Support pressure sensitivity if available

**Libraries:** None (custom canvas implementation)
**Files:** `src/primitives/signature-pad.tsx`

### 2.5 Whiteboard / Drawing Canvas
**Technical Approach:**
- Canvas-based with tool palette (pen, eraser, shapes, text)
- History stack for undo/redo
- Export to image

**Libraries:** None (custom canvas implementation)
**Files:** `src/primitives/whiteboard.tsx`, `src/primitives/drawing-canvas.tsx`

---

## 3. Native Mobile Components

### 3.1 Navigation Rail
**Technical Approach:**
- Vertical variant of `BottomNav`
- Use `flex-col` layout, icon + label below
- Support expanded/collapsed states

**Files:** `src/composites/navigation-rail.tsx`

### 3.2 Bottom Sheet
**Technical Approach:**
- Use `@radix-ui/react-dialog` with `side="bottom"`
- Add snap points support (25%, 50%, 90%)
- Implement drag handle with touch events

**Files:** `src/composites/bottom-sheet.tsx`

### 3.3 Action Sheet
**Technical Approach:**
- Mobile-native style action menu
- Use `@radix-ui/react-dialog` with destructive/default actions
- Support icons and descriptions

**Files:** `src/composites/action-sheet.tsx`

### 3.4 Swipeable Cards
**Technical Approach:**
- Touch event handlers (`touchstart`, `touchmove`, `touchend`)
- Implement snap-back animation on release
- Support left/right swipe actions with callbacks

**Libraries:** None (custom touch handling)
**Files:** `src/primitives/swipeable-card.tsx`

### 3.5 Floating Toolbar
**Technical Approach:**
- Fixed position toolbar with elevation
- Support primary/secondary actions
- Auto-hide on scroll down, show on scroll up

**Files:** `src/composites/floating-toolbar.tsx`

---

## 4. Advanced UI Patterns & Orchestration

### 4.1 VirtualizedList
**Technical Approach:**
- Calculate visible window based on `scrollTop` and container height
- Use absolute positioning for items outside viewport
- Support dynamic row heights with measurement cache

**Libraries:** `@tanstack/react-virtual` (preferred) or custom implementation
**Files:** `src/composites/virtualized-list.tsx`

### 4.2 Infinite Scroll System
**Technical Approach:**
- IntersectionObserver sentinel element at bottom
- Debounced scroll handler as fallback
- State machine: `idle` → `loading` → `success` | `error` | `complete`

**Files:** `src/composites/infinite-scroll.tsx`, `src/hooks/useInfiniteScroll.ts`

### 4.3 Generalized Drag & Drop
**Technical Approach:**
- HTML5 Drag and Drop API with custom drag image
- Drop zones with visual feedback
- Sortable list support

**Libraries:** `@dnd-kit/core` (preferred) or `react-dnd`
**Files:** `src/primitives/drag-drop-context.tsx`, `src/primitives/draggable.tsx`, `src/primitives/droppable.tsx`

### 4.4 Focus Trapping
**Technical Approach:**
- Use `@radix-ui/react-focus-guards` or custom implementation
- Trap focus within modal/dialog boundaries
- Return focus to trigger element on close

**Files:** `src/primitives/focus-trap.tsx`

### 4.5 Managed Modal Stack
**Technical Approach:**
- Context-based modal registry
- Support nested modals with z-index management
- Keyboard navigation (Escape to close, Tab trapping)

**Files:** `src/composites/modal-stack.tsx`, `src/hooks/useModalStack.ts`

---

## 5. Complete Form Patterns

### 5.1 Login Form
**Technical Approach:**
- Email + password fields with validation
- "Remember me" checkbox
- Social login placeholders
- Error states and loading states

**Files:** `src/composites/forms/login-form.tsx`

### 5.2 Registration Form
**Technical Approach:**
- Multi-step: Account → Profile → Preferences
- Password strength indicator
- Terms acceptance
- Email verification placeholder

**Files:** `src/composites/forms/register-form.tsx`

### 5.3 Two-Factor Authentication (2FA)
**Technical Approach:**
- OTP input (6 digits) with auto-focus
- Backup codes section
- QR code scanner fallback
- TOTP setup placeholder

**Files:** `src/composites/forms/two-factor-form.tsx`

---

## 6. Branding & Visual Assets

### 6.1 Mascot Integration
**Technical Approach:**
- SVG-based mascot with pose variations
- Animated variants using CSS or Lottie
- Context-aware placement (empty states, onboarding)

**Files:** `src/primitives/mascot.tsx`, `assets/mascot/`

### 6.2 3D Illustrations
**Technical Approach:**
- CSS 3D transforms for simple 3D effects
- Three.js for complex 3D scenes (if needed)
- Responsive 3D containers

**Libraries:** `three`, `@react-three/fiber` (optional)
**Files:** `src/primitives/three-d-illustration.tsx`

### 6.3 Animated Logo
**Technical Approach:**
- SVG path animation for logo reveal
- State-based animation (loading, active, inactive)
- Reduced motion support

**Files:** `src/primitives/animated-logo.tsx`

### 6.4 Watermark
**Technical Approach:**
- Fixed position overlay with low opacity
- Repeat pattern for full-page coverage
- Prevent user selection

**Files:** `src/primitives/watermark.tsx`

### 6.5 Brand Patterns
**Technical Approach:**
- SVG pattern definitions for backgrounds
- CSS `background-image` with data URIs
- Responsive scaling

**Files:** `src/primitives/brand-pattern.tsx`

---

## 7. Media Handling

### 7.1 Lazy Loading Images
**Technical Approach:**
- IntersectionObserver for native lazy loading
- Placeholder/shimmer during load
- Error state with retry

**Files:** `src/primitives/lazy-image.tsx`

### 7.2 Responsive Image Scaling
**Technical Approach:**
- `srcset` and `sizes` attributes
- Art direction with `<picture>` element
- Automatic format selection (WebP/AVIF)

**Files:** `src/primitives/responsive-image.tsx`

### 7.3 Masonry Layout
**Technical Approach:**
- CSS columns for simple masonry
- Grid-based for controlled layouts
- Responsive breakpoints

**Files:** `src/composites/masonry-layout.tsx`

### 7.4 Carousel with Dots
**Technical Approach:**
- Touch swipe + button navigation
- Auto-play with pause on hover
- Dot indicators with active state
- Accessibility: arrow key navigation

**Files:** `src/composites/carousel.tsx`

---

## Implementation Priority

### Phase 1 (High Impact, Low Effort)
1. Carousel with Dots
2. Masonry Layout
3. Lazy Image
4. Responsive Image
5. Staggered Animations
6. Bottom Sheet
7. Action Sheet

### Phase 2 (Medium Complexity)
1. VirtualizedList
2. Infinite Scroll
3. Drag & Drop Framework
4. Login/Register/2FA Forms
5. Swipeable Cards
6. Navigation Rail
7. Animated Logo

### Phase 3 (Advanced Features)
1. Lottie Integration
2. Spring Physics
3. Parallax Effects
4. Shared Element Transitions
5. QR/Barcode Scanner
6. Signature Pad
7. Whiteboard/Drawing Canvas
8. 3D Illustrations
9. Focus Trap
10. Modal Stack

---

## Technical Best Practices

### Performance
- Use `React.memo` for expensive components
- Implement `useMemo`/`useCallback` for event handlers
- Lazy load heavy components with `React.lazy()`
- Use CSS transforms for animations (GPU accelerated)
- Implement virtualization for lists > 100 items

### Accessibility
- All interactive elements must be keyboard accessible
- Provide `aria-label` and `role` attributes
- Support `prefers-reduced-motion` media query
- Ensure sufficient color contrast (WCAG AA)

### Scalability
- Compound component pattern for complex UI
- Render props for flexible customization
- Context API for shared state
- Consistent naming: `kebab-case` for files, `PascalCase` for components

### Testing Strategy
- Unit tests for hooks and utilities
- Component tests with `@testing-library/react`
- Visual regression tests for critical components
- E2E tests for form flows

---

## File Structure

```
packages/ui/src/
├── primitives/
│   ├── lottie-player.tsx
│   ├── lottie-icon.tsx
│   ├── spring-motion.tsx
│   ├── swipeable-card.tsx
│   ├── signature-pad.tsx
│   ├── whiteboard.tsx
│   ├── drawing-canvas.tsx
│   ├── stopwatch.tsx
│   ├── clock.tsx
│   ├── weather-widget.tsx
│   ├── stock-ticker.tsx
│   ├── qr-scanner.tsx
│   ├── navigation-rail.tsx
│   ├── lazy-image.tsx
│   ├── responsive-image.tsx
│   ├── animated-logo.tsx
│   ├── watermark.tsx
│   ├── brand-pattern.tsx
│   ├── drag-drop-context.tsx
│   ├── draggable.tsx
│   ├── droppable.tsx
│   └── focus-trap.tsx
├── composites/
│   ├── parallax-section.tsx
│   ├── stagger-container.tsx
│   ├── shared-element-transition.tsx
│   ├── bottom-sheet.tsx
│   ├── action-sheet.tsx
│   ├── floating-toolbar.tsx
│   ├── virtualized-list.tsx
│   ├── infinite-scroll.tsx
│   ├── modal-stack.tsx
│   ├── forms/
│   │   ├── login-form.tsx
│   │   ├── register-form.tsx
│   │   └── two-factor-form.tsx
│   ├── carousel.tsx
│   ├── masonry-layout.tsx
│   └── three-d-illustration.tsx
├── hooks/
│   ├── useSpring.ts
│   ├── useParallax.ts
│   ├── useInfiniteScroll.ts
│   ├── useStopwatch.ts
│   └── useSharedElement.ts
└── assets/
    ├── mascot/
    ├── animations/
    └── patterns/
```

---

## Dependencies to Add

```json
{
  "dependencies": {
    "lottie-web": "^5.12.2",
    "@lottiefiles/react-lottie-player": "^3.5.0",
    "@zxing/browser": "^0.1.4",
    "@dnd-kit/core": "^6.1.0",
    "@dnd-kit/sortable": "^8.0.0",
    "@dnd-kit/utilities": "^3.2.2",
    "three": "^0.160.0",
    "@react-three/fiber": "^8.15.0"
  }
}
```

---

## Next Steps

1. Review and approve this plan
2. Implement Phase 1 components (estimated: 2-3 days)
3. Run type-check and build after each phase
4. Visual verification on dev server
5. Document usage examples in `DESIGN_SYSTEM.md`
