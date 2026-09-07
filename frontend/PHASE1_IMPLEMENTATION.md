# Phase 1 Implementation Guide — Day 1-3

> Target: `@eco/ui` package
> Duration: 2-3 days
> Components: Carousel, Masonry Layout, Lazy Image, Bottom Sheet, Action Sheet, Form Patterns

---

## Day 1: Media Components (Carousel, Masonry, Lazy Image)

### 1.1 Carousel with Dots

**File:** `packages/ui/src/composites/carousel.tsx`

**Technical Approach:**
- Touch-enabled swipe with `touchstart/touchmove/touchend`
- CSS transform for slide transitions (GPU accelerated)
- Auto-play with `useInterval` hook
- Pause on hover/focus
- Keyboard navigation (arrow keys)
- Dot indicators with active state

**Key Implementation Details:**

```tsx
// Core structure
<Carousel>
  <CarouselContent>
    <CarouselItem>...</CarouselItem>
    <CarouselItem>...</CarouselItem>
  </CarouselContent>
  <CarouselPrevious />
  <CarouselNext />
  <CarouselDots />
</Carousel>
```

**Performance Considerations:**
- Use `transform: translateX()` instead of `left` property
- Implement `will-change: transform` during animation
- Debounce resize events
- Lazy load non-visible slides with `loading="lazy"`
- Limit auto-play to 3-5 seconds

**Accessibility:**
- `role="region"` with `aria-roledescription="carousel"`
- `aria-label` on each slide
- Live region for slide count
- Pause auto-play on focus

---

### 1.2 Masonry Layout

**File:** `packages/ui/src/composites/masonry-layout.tsx`

**Technical Approach:**
- CSS `column-count` for simple masonry (most performant)
- CSS Grid with `grid-row-end: span` for controlled layouts
- Responsive breakpoints: 1 col (mobile) → 2 col (tablet) → 3-4 col (desktop)

**Key Implementation Details:**

```tsx
// CSS-based approach (preferred for performance)
<MasonryLayout columns={3} gap="md">
  <MasonryItem>...</MasonryItem>
  <MasonryItem>...</MasonryItem>
</MasonryLayout>
```

**Performance Considerations:**
- Use CSS `column-count` over JavaScript positioning
- Avoid layout thrashing with `content-visibility: auto`
- Set explicit `break-inside: avoid` on items
- Use `contain: layout style paint` for isolation

**Best Practices:**
- Maintain aspect ratios with `aspect-ratio` CSS
- Use `object-fit: cover` for images
- Provide skeleton loaders for dynamic content

---

### 1.3 Lazy Loading Images

**File:** `packages/ui/src/primitives/lazy-image.tsx`

**Technical Approach:**
- Native `loading="lazy"` attribute as baseline
- `IntersectionObserver` for custom placeholder/blur-up
- Low-quality image placeholder (LQIP) technique
- Error boundary with retry mechanism

**Key Implementation Details:**

```tsx
<LazyImage
  src="image.jpg"
  placeholder="blur" // or shimmer
  blurDataURL="data:image/..."
  alt="Description"
/>
```

**Performance Considerations:**
- Use `srcset` with multiple resolutions
- Implement `sizes` attribute for responsive images
- Cache observed entries in `Set` to avoid re-observation
- Unobserve after load to free resources
- Use WebP/AVIF formats with fallbacks

**Best Practices:**
- Always provide `alt` text for accessibility
- Set explicit `width` and `height` to prevent CLS
- Use `fetchpriority="high"` for above-fold images
- Implement error state with fallback image

---

## Day 2: Bottom Sheet & Action Sheet

### 2.1 Bottom Sheet

**File:** `packages/ui/src/composites/bottom-sheet.tsx`

**Technical Approach:**
- Radix Dialog with `side="bottom"`
- Snap points: `25%`, `50%`, `90%` of viewport
- Drag handle with touch/mouse events
- Backdrop with blur effect
- Snap animation with spring physics

**Key Implementation Details:**

```tsx
<BottomSheet open={open} onOpenChange={setOpen} snapPoints={['25%', '50%', '90%']}>
  <BottomSheetTrigger>Open</BottomSheetTrigger>
  <BottomSheetContent>
    <BottomSheetHandle />
    {/* Content */}
  </BottomSheetContent>
</BottomSheet>
```

**Performance Considerations:**
- Use `transform: translateY()` for animations
- Implement `overscroll-behavior: contain` to prevent body scroll
- Lock body scroll when open
- Use `will-change: transform` during drag

**Accessibility:**
- Focus trap within sheet
- Return focus to trigger on close
- Escape key closes sheet
- `aria-modal="true"` and `role="dialog"`

**Best Practices:**
- Support swipe down to dismiss
- Show visual indicator for drag handle
- Disable page scroll when sheet is open
- Snap to nearest point on release

---

### 2.2 Action Sheet

**File:** `packages/ui/src/composites/action-sheet.tsx`

**Technical Approach:**
- Radix Dialog with bottom positioning
- Group actions: destructive, default, cancel
- Icon support for actions
- Haptic feedback simulation (visual)

**Key Implementation Details:**

```tsx
<ActionSheet open={open} onOpenChange={setOpen}>
  <ActionSheetContent>
    <ActionSheetGroup>
      <ActionSheetAction icon={<Share />}>Share</ActionSheetAction>
      <ActionSheetAction destructive>Delete</ActionSheetAction>
    </ActionSheetGroup>
    <ActionSheetCancel>Cancel</ActionSheetCancel>
  </ActionSheetContent>
</ActionSheet>
```

**Performance Considerations:**
- Minimal animations (fade + slide up)
- Fast close on action selection
- Prevent scroll on body

**Accessibility:**
- Destructive actions clearly labeled
- Cancel button always visible
- Focus management

---

## Day 3: Form Patterns

### 3.1 Login Form

**File:** `packages/ui/src/composites/forms/login-form.tsx`

**Technical Approach:**
- Controlled inputs with validation
- Email format validation with regex
- Password visibility toggle
- "Remember me" checkbox
- Loading state with disabled submit
- Error display with accessible messaging

**Key Implementation Details:**

```tsx
<LoginForm
  onSubmit={async (credentials) => {
    // handle login
  }}
  onForgotPassword={() => {}}
  onSignUp={() => {}}
/>
```

**Validation Rules:**
- Email: RFC 5322 regex
- Password: min 8 chars, 1 uppercase, 1 number
- Real-time validation on blur
- Error messages in Persian

**Performance Considerations:**
- Debounce validation (300ms)
- Memoize validation functions
- Disable submit during submission

---

### 3.2 Registration Form

**File:** `packages/ui/src/composites/forms/register-form.tsx`

**Technical Approach:**
- Multi-step: Account → Profile → Preferences
- Step indicator with Stepper component
- Password strength meter
- Terms acceptance with link
- Email verification placeholder

**Key Implementation Details:**

```tsx
<RegisterForm
  onSubmit={async (data) => {
    // handle registration
  }}
  steps={[
    { title: 'Account', fields: ['email', 'password'] },
    { title: 'Profile', fields: ['name', 'avatar'] },
    { title: 'Preferences', fields: ['theme', 'notifications'] }
  ]}
/>
```

**Validation Rules:**
- Password strength: 0-4 score with visual indicator
- Confirm password match
- Name: min 2 characters
- Terms must be accepted

---

### 3.3 Two-Factor Authentication (2FA)

**File:** `packages/ui/src/composites/forms/two-factor-form.tsx`

**Technical Approach:**
- 6-digit OTP input with auto-focus
- Paste support (detect 6-digit code in clipboard)
- Countdown timer for code expiration
- Backup codes section (expandable)
- QR code fallback for TOTP apps

**Key Implementation Details:**

```tsx
<TwoFactorForm
  onSubmit={async (code) => {
    // verify code
  }}
  onBack={() => {}}
  onUseBackupCode={() => {}}
  resendTimer={30}
/>
```

**Validation Rules:**
- 6 digits only
- Auto-submit when all digits entered
- Error shake animation on invalid code
- Rate limiting placeholder

---

## Shared Utilities

### useInterval Hook

```tsx
function useInterval(callback: () => void, delay: number | null) {
  useEffect(() => {
    if (delay === null) return;
    const id = setInterval(callback, delay);
    return () => clearInterval(id);
  }, [callback, delay]);
}
```

### useSwipeable Hook

```tsx
function useSwipeable({
  onSwipeLeft,
  onSwipeRight,
  threshold = 50
}: SwipeableOptions) {
  // Touch event handlers with velocity calculation
}
```

### Form Validation Utilities

```tsx
const validators = {
  email: (value: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
  password: (value: string) => value.length >= 8 && /[A-Z]/.test(value) && /\d/.test(value),
  required: (value: string) => value.trim().length > 0,
};
```

---

## Testing Checklist

### Carousel
- [ ] Swipe left/right works
- [ ] Dot indicators update correctly
- [ ] Auto-play pauses on hover
- [ ] Keyboard navigation works
- [ ] Infinite loop option works

### Masonry
- [ ] Items flow correctly in columns
- [ ] Responsive breakpoints work
- [ ] No horizontal overflow
- [ ] Images maintain aspect ratio

### Lazy Image
- [ ] Placeholder shows while loading
- [ ] Image loads when in viewport
- [ ] Error state displays fallback
- [ ] CLS is prevented

### Bottom Sheet
- [ ] Opens/closes smoothly
- [ ] Snap points work correctly
- [ ] Drag handle dismisses sheet
- [ ] Body scroll is locked
- [ ] Focus trap works

### Action Sheet
- [ ] Actions trigger callbacks
- [ ] Destructive actions styled correctly
- [ ] Cancel button dismisses sheet
- [ ] backdrop click closes sheet

### Forms
- [ ] Validation shows errors
- [ ] Submit button disabled during loading
- [ ] Password visibility toggle works
- [ ] OTP auto-focus works
- [ ] Step navigation works

---

## Performance Budgets

| Component | Target | Budget |
|-----------|--------|--------|
| Carousel | < 50KB | 50KB gzip |
| Masonry | < 5KB | 5KB gzip |
| Lazy Image | < 3KB | 3KB gzip |
| Bottom Sheet | < 8KB | 8KB gzip |
| Action Sheet | < 6KB | 6KB gzip |
| Forms | < 15KB | 15KB gzip |

---

## Dependencies to Install

```bash
pnpm add lottie-web @lottiefiles/react-lottie-player @zxing/browser @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities three @react-three/fiber
```

---

## File Structure

```
packages/ui/src/
├── composites/
│   ├── carousel.tsx
│   ├── masonry-layout.tsx
│   ├── bottom-sheet.tsx
│   ├── action-sheet.tsx
│   ├── forms/
│   │   ├── login-form.tsx
│   │   ├── register-form.tsx
│   │   └── two-factor-form.tsx
├── primitives/
│   ├── lazy-image.tsx
├── hooks/
│   ├── useSwipeable.ts
│   ├── useInterval.ts
│   └── useLazyImage.ts
└── utils/
    ├── validators.ts
    └── form-utils.ts
```

---

## Next Steps

1. Review this implementation guide
2. Start with Carousel (most reusable)
3. Implement Masonry Layout
4. Add Lazy Image primitive
5. Build Bottom Sheet & Action Sheet
6. Create Form Patterns
7. Run type-check and build
8. Visual verification on dev server
