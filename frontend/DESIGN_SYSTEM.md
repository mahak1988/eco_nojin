# Eco Nojin Design System

## Typography Scale

| Role | CSS class | Usage |
|------|-----------|-------|
| `display` | `text-display` | Hero page titles |
| `h1` | `text-h1` | Page headings |
| `h2` | `text-h2` | Section headings |
| `h3` | `text-h3` | Card titles |
| `h4` | `text-h4` | Inline labels |
| `bodyLg` | `text-bodyLg` | Lead paragraphs |
| `body` | `text-body` | Body text |
| `bodySm` | `text-bodySm` | Secondary text |
| `caption` | `text-caption` | Captions, metadata |
| `overline` | `text-overline` | Overlines, badges |

Weights: `font-thin` … `font-black` via `fontWeight` map.

## Semantic Color Tokens

```ts
semanticTokens: {
  soil, water, carbon, vegetation, climate, satellite,
  success, warning, danger, info, neutral
}
```

Helpers: `tokenToBgClass(token)`, `tokenToTextClass(token)`.

## Spacing Scale

`numericSpacing` (0–96) maps to Tailwind `spacing` scale. `semanticSpacing` aliases: `componentXS` … `pageLG`.

## Dark Mode Contract

- Toggle via `ThemeToggle` component (sets `class="dark"` on `<html>`).
- Persisted in `localStorage` under key `eco.theme`.
- Falls back to `prefers-color-scheme`.
- All tokens defined in `tokens.css` with `:root.dark` overrides.

## Migration Guide

Replace ad-hoc utilities with semantic roles:

```tsx
// Before
<h1 className="text-4xl font-bold tracking-tight">Title</h1>

// After
<h1 className="text-h1 font-bold">Title</h1>
```

## Component Library (@eco/ui)

### Primitives

| Component | Description |
|-----------|-------------|
| `Button` | Primary/secondary/ghost/destructive variants |
| `Input` | Text input with validation states |
| `Textarea` | Multi-line text input |
| `Badge` | Status badges with semantic tones |
| `Card` | Container with header/body/footer |
| `Avatar` | User avatar with fallback |
| `Spinner` | Loading spinner |
| `Skeleton` | Placeholder skeleton |
| `Field` | Form field wrapper with label/error |
| `Select` | Dropdown select (Radix) |
| `Checkbox` | Checkbox input |
| `RadioGroup` | Radio button group |
| `Switch` | Toggle switch |
| `Slider` | Range slider |
| `Progress` | Linear progress bar |
| `CircularProgress` | Circular progress indicator |
| `Chip` | Removable tag/chip |
| `AvatarGroup` | Grouped avatars with overflow |
| `Breadcrumb` | Navigation breadcrumb |
| `Pagination` | Page navigation |
| `Stepper` | Multi-step indicator |
| `Accordion` | Collapsible sections |
| `Collapsible` | Simple collapsible |
| `ScrollArea` | Custom scrollbar |
| `Separator` | Visual divider |
| `ResizablePanelGroup` | Resizable split panels |
| `ToggleGroup` | Toggle button group |
| `SegmentedControl` | Segmented control |
| `Rating` | Star rating |
| `Countdown` | Countdown timer |
| `FileUpload` | Drag & drop file upload |
| `DatePicker` | Date selection |
| `TimePicker` | Time selection |
| `OTPInput` | One-time password input |
| `ColorPicker` | Color selection |
| `Calendar` | Calendar widget |
| `MentionInput` | Text input with mentions |
| `RichTextEditor` | WYSIWYG editor |
| `Toggle` | Toggle button |
| `SkeletonText` | Text skeleton loader |
| `Shimmer` | Shimmer effect |
| `LazyImage` | Lazy loading image |
| `ResponsiveImage` | Responsive image with srcSet |
| `Watermark` | Watermark overlay |
| `BrandPattern` | Brand pattern background |
| `FocusTrap` | Focus trapping utility |
| `Stopwatch` | Stopwatch widget |
| `Clock` | Digital clock |
| `WeatherWidget` | Weather display |
| `StockTicker` | Stock ticker |
| `QRScanner` | QR code scanner |
| `SignaturePad` | Signature capture |
| `Whiteboard` | Drawing whiteboard |
| `DrawingCanvas` | Simple drawing canvas |
| `Mascot` | Brand mascot |
| `ThreeDIllustration` | 3D illustration container |

### Composites

| Component | Description |
|-----------|-------------|
| `Tabs` | Tabbed content |
| `Dialog` | Modal dialog |
| `Dropdown` | Dropdown menu |
| `Popover` | Popover overlay |
| `Tooltip` | Tooltip |
| `Toast` | Toast notifications |
| `Alert` | Alert banner |
| `EmptyState` | Empty state placeholder |
| `DataTable` | Sortable data table |
| `ResultCard` | Result display card |
| `StatCard3D` | 3D stat card |
| `GlassCard` | Glassmorphism card |
| `ChartCard` | Chart container |
| `Sparkline` | Mini sparkline chart |
| `PieChart` | Pie chart |
| `DataGrid` | Advanced data grid |
| `TreeView` | Tree view navigation |
| `Timeline` | Timeline component |
| `KanbanBoard` | Kanban board |
| `BottomNav` | Bottom navigation |
| `TopNav` | Top navigation bar |
| `NavigationRail` | Side navigation rail |
| `ChatBubble` | Chat message bubble |
| `MessageThread` | Message thread |
| `ProductCard` | Product card |
| `CartDrawer` | Shopping cart drawer |
| `PricingCard` | Pricing card |
| `ReviewCard` | Review/comment card |
| `DashboardLayout` | Dashboard shell layout |
| `WidgetGrid` | Widget grid container |
| `ImageGallery` | Image gallery with lightbox |
| `VideoPlayer` | Video player |
| `AudioPlayer` | Audio player |
| `SettingsSection` | Settings section |
| `NotificationCenter` | Notification center |
| `AlertBanner` | Alert banner |
| `InlineValidation` | Inline validation message |
| `PullToRefresh` | Pull to refresh |
| `SearchOverlay` | Search overlay |
| `FormWizard` | Multi-step form wizard |
| `MegaMenu` | Mega navigation menu |
| `OffCanvas` | Off-canvas drawer |
| `SplitView` | Split view layout |
| `StickyHeader` | Sticky header |
| `AnimatedCounter` | Animated number counter |
| `RippleEffect` | Ripple effect container |
| `Carousel` | Image carousel with dots |
| `MasonryLayout` | Masonry grid layout |
| `BottomSheet` | Bottom sheet with snap points |
| `ActionSheet` | Mobile action sheet |
| `LoginForm` | Login form template |
| `RegisterForm` | Multi-step registration form |
| `TwoFactorForm` | 2FA verification form |
| `VirtualizedList` | Virtualized list |
| `InfiniteScroll` | Infinite scroll container |
| `FloatingToolbar` | Floating action toolbar |
| `ModalStack` | Managed modal stack |
| `ParallaxSection` | Parallax scroll section |
| `StaggerContainer` | Staggered animation container |
| `SharedElementTransition` | Shared element transition |

### Hooks

| Hook | Description |
|------|-------------|
| `useSwipeable` | Swipe gesture detection |
| `useInterval` | SetInterval with cleanup |
| `useLazyImage` | Lazy image loading |
| `useStopwatch` | Stopwatch timer logic |
| `useSpring` | Spring physics animation |

## Animations

| Class | Description |
|-------|-------------|
| `animate-in-up` | Fade in from bottom |
| `animate-in-fade` | Simple fade in |
| `animate-slide-up` | Slide up |
| `animate-slide-down` | Slide down |
| `animate-slide-in-left` | Slide from left |
| `animate-slide-in-right` | Slide from right |
| `animate-scale-in` | Scale in |
| `animate-ripple` | Ripple effect |
| `animate-pulse` | Pulse (shimmer) |

## Accessibility (A11y)

- All interactive elements have `focus:outline-none focus:shadow-glow`
- ARIA labels on icon-only buttons
- `sr-only` class for screen-reader-only text
- `role` attributes on composite components
- Keyboard navigation support
- `prefers-reduced-motion` respected

## Performance Guidelines

- Use `transform` and `opacity` for animations (GPU accelerated)
- Implement virtualization for lists > 100 items
- Lazy load images with `loading="lazy"`
- Use `will-change-transform` sparingly
- Debounce scroll handlers
- Use `React.memo` for expensive components

## File Structure

```
packages/ui/src/
├── primitives/          # Atomic components (~50)
├── composites/          # Composed components (~40)
├── hooks/               # Custom hooks (~5)
├── utils/               # Utilities (validators, cn)
├── tokens/              # Design tokens
└── index.ts             # Main export
```

## Usage

```tsx
import {
  Button,
  Card,
  Input,
  Carousel,
  MasonryLayout,
  BottomSheet,
  LoginForm,
  VirtualizedList,
  LottiePlayer,
  AnimatedLogo,
} from '@eco/ui';
```
