import { type SVGProps, forwardRef } from 'react'

export type IconName =
  | 'leaf'
  | 'droplet'
  | 'sun'
  | 'cloud'
  | 'satellite'
  | 'coin'
  | 'chart'
  | 'sparkles'
  | 'shield'
  | 'bolt'
  | 'map'
  | 'database'
  | 'cpu'
  | 'flask'
  | 'waves'
  | 'gauge'
  | 'bell'
  | 'search'
  | 'globe'
  | 'mountain'
  | 'sprout'
  | 'check'
  | 'x'
  | 'menu'
  | 'arrow'
  | 'settings'
  | 'user'
  | 'chevron-down'
  | 'chevron-left'
  | 'chevron-right'
  | 'alert-triangle'
  | 'info'
  | 'check-circle-2'
  | 'x-circle'
  | 'play'
  | 'pause'
  | 'skip-back'
  | 'skip-forward'
  | 'volume-2'
  | 'maximize'
  | 'star'
  | 'upload-cloud'
  | 'bell'

type El =
  | { t: 'path'; d: string }
  | { t: 'circle'; cx: number; cy: number; r: number }
  | { t: 'rect'; x: number; y: number; width: number; height: number }
  | { t: 'polygon'; points: string }
  | { t: 'line'; x1: string; y1: string; x2: string; y2: string }

const ICONS: Record<IconName, El[]> = {
  leaf: [
    {
      t: 'path',
      d: 'M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.5 19 2c1 2 2 4.2 2 8 0 5.5-4.8 10-10 10Z',
    },
    { t: 'path', d: 'M2 21c0-3 1.9-5.4 5.1-6C9.5 14.5 12 13 13 12' },
  ],
  droplet: [
    {
      t: 'path',
      d: 'M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z',
    },
  ],
  sun: [
    { t: 'circle', cx: 12, cy: 12, r: 4 },
    {
      t: 'path',
      d: 'M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M6.3 17.7l-1.4 1.4M19.1 4.9l-1.4 1.4',
    },
  ],
  cloud: [{ t: 'path', d: 'M17.5 19H9a7 7 0 1 1 6.7-9h1.8a4.5 4.5 0 1 1 0 9Z' }],
  satellite: [
    { t: 'path', d: 'M13 7 9 3 5 7l4 4' },
    { t: 'path', d: 'm17 11 4 4-4 4-4-4' },
    { t: 'path', d: 'm8 12 4 4 6-6-4-4Z' },
    { t: 'path', d: 'm16 8 3-3' },
    { t: 'path', d: 'M9 21a6 6 0 0 0-6-6' },
  ],
  coin: [
    { t: 'circle', cx: 12, cy: 12, r: 8 },
    { t: 'path', d: 'M12 8v8M9.5 10h5M9.5 14h5' },
  ],
  chart: [
    { t: 'path', d: 'M3 3v18h18' },
    { t: 'path', d: 'M7 16v-5M12 16V8M17 16v-8' },
  ],
  sparkles: [
    { t: 'path', d: 'M12 3l1.9 5.8 5.8 1.9-5.8 1.9L12 18.4l-1.9-5.8L4.3 10.7l5.8-1.9Z' },
    { t: 'path', d: 'M5 3v4M3 5h4M19 17v4M17 19h4' },
  ],
  shield: [{ t: 'path', d: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z' }],
  bolt: [{ t: 'path', d: 'M13 2 3 14h9l-1 8 10-12h-9l1-8z' }],
  map: [
    { t: 'path', d: 'M9 3 6 5v16l3-2 6 2 3-2V3l-3 2-6-2Z' },
    { t: 'path', d: 'M9 3v16M15 5v16' },
  ],
  database: [
    { t: 'circle', cx: 12, cy: 5, r: 9 },
    { t: 'path', d: 'M3 5v14c0 1.7 4 3 9 3s9-1.3 9-3V5' },
    { t: 'path', d: 'M3 12c0 1.7 4 3 9 3s9-1.3 9-3' },
  ],
  cpu: [
    { t: 'path', d: 'M6 4h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z' },
    { t: 'path', d: 'M9 9h6v6H9z' },
    { t: 'path', d: 'M9 2v2M15 2v2M9 20v2M15 20v2M2 9h2M2 15h2M20 9h2M20 15h2' },
  ],
  flask: [
    { t: 'path', d: 'M6 3v16a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V3' },
    { t: 'path', d: 'M4.5 3h15M6 14h12' },
  ],
  waves: [
    { t: 'path', d: 'M2 6c2.5 0 2.5 3 5 3s2.5-3 5-3 2.5 3 5 3 2.5-3 5-3' },
    { t: 'path', d: 'M2 12c2.5 0 2.5 3 5 3s2.5-3 5-3 2.5 3 5 3 2.5-3 5-3' },
    { t: 'path', d: 'M2 18c2.5 0 2.5 3 5 3s2.5-3 5-3 2.5 3 5 3 2.5-3 5-3' },
  ],
  gauge: [
    { t: 'path', d: 'm12 14 4-4' },
    { t: 'path', d: 'M3.3 19a10 10 0 1 1 17.4 0' },
  ],
  bell: [
    { t: 'path', d: 'M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9' },
    { t: 'path', d: 'M10.3 21a1.9 1.9 0 0 0 3.4 0' },
  ],
  search: [
    { t: 'circle', cx: 11, cy: 11, r: 8 },
    { t: 'path', d: 'm21 21-4.3-4.3' },
  ],
  globe: [
    { t: 'circle', cx: 12, cy: 12, r: 10 },
    { t: 'path', d: 'M2 12h20' },
    {
      t: 'path',
      d: 'M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z',
    },
  ],
  mountain: [{ t: 'path', d: 'm8 3 4 8 5-5 5 15H2L8 3z' }],
  sprout: [
    { t: 'path', d: 'M12 20v-8' },
    { t: 'path', d: 'M12 12c0-4 2.5-6 8-6 0 4-2.5 6-8 6Z' },
    { t: 'path', d: 'M12 14c0-3-2-4.5-6-4.5 0 3 2 4.5 6 4.5Z' },
  ],
  check: [{ t: 'path', d: 'M20 6 9 17l-5-5' }],
  x: [{ t: 'path', d: 'M18 6 6 18M6 6l12 12' }],
  menu: [{ t: 'path', d: 'M4 6h16M4 12h16M4 18h16' }],
  arrow: [
    { t: 'path', d: 'M5 12h14' },
    { t: 'path', d: 'm12 5 7 7-7 7' },
  ],
  settings: [
    { t: 'path', d: 'M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3' },
    { t: 'path', d: 'M1 14h6M9 8h6M17 16h6' },
  ],
  user: [
    { t: 'circle', cx: 12, cy: 8, r: 4 },
    { t: 'path', d: 'M4 21c0-4 3.6-6 8-6s8 2 8 6' },
  ],
  'chevron-down': [{ t: 'path', d: 'm6 9 6 6 6-6' }],
  'chevron-left': [{ t: 'path', d: 'm15 18-6-6 6-6' }],
  'chevron-right': [{ t: 'path', d: 'm9 18 6-6-6-6' }],
  'alert-triangle': [
    { t: 'path', d: 'm21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z' },
    { t: 'path', d: 'M12 9v4M12 17h.01' },
  ],
  info: [
    { t: 'circle', cx: 12, cy: 12, r: 10 },
    { t: 'path', d: 'M12 16v-4M12 8h.01' },
  ],
  'check-circle-2': [
    { t: 'path', d: 'M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z' },
    { t: 'path', d: 'm9 12 2 2 4-4' },
  ],
  'x-circle': [
    { t: 'path', d: 'M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z' },
    { t: 'path', d: 'm15 9-6 6M9 9l6 6' },
  ],
  play: [{ t: 'polygon', points: '6 3 20 12 6 21 6 3' }],
  pause: [
    { t: 'rect', x: 6, y: 4, width: 4, height: 16 },
    { t: 'rect', x: 14, y: 4, width: 4, height: 16 },
  ],
  'skip-back': [
    { t: 'polygon', points: '19 20 9 12 19 4 19 20' },
    { t: 'line', x1: '5', y1: '19', x2: '5', y2: '5' },
  ],
  'skip-forward': [
    { t: 'polygon', points: '5 4 15 12 5 20 5 4' },
    { t: 'line', x1: '19', y1: '5', x2: '19', y2: '19' },
  ],
  'volume-2': [
    { t: 'polygon', points: '11 5 6 9 2 9 2 15 6 15 11 19 11 5' },
    { t: 'path', d: 'M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07' },
  ],
  maximize: [
    {
      t: 'path',
      d: 'M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3',
    },
  ],
  star: [
    {
      t: 'polygon',
      points:
        '12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2',
    },
  ],
  'upload-cloud': [
    { t: 'path', d: 'M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242' },
    { t: 'path', d: 'M12 12v9M8 17l4-5 4 5' },
  ],
}

export interface IconProps extends SVGProps<SVGSVGElement> {
  name: IconName
  size?: number
}

export const Icon = forwardRef<SVGSVGElement, IconProps>(({ name, size = 20, ...props }, ref) => (
  <svg
    ref={ref}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={2}
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
    {...props}
  >
    {ICONS[name].map((el, i) => {
      if (el.t === 'circle') return <circle key={i} cx={el.cx} cy={el.cy} r={el.r} />
      if (el.t === 'rect')
        return <rect key={i} x={el.x} y={el.y} width={el.width} height={el.height} />
      if (el.t === 'polygon') return <polygon key={i} points={el.points} />
      if (el.t === 'line') return <line key={i} x1={el.x1} y1={el.y1} x2={el.x2} y2={el.y2} />
      return <path key={i} d={el.d} />
    })}
  </svg>
))
Icon.displayName = 'Icon'

const ICON_ALIASES: Record<string, IconName> = {
  Check: 'check',
  X: 'x',
  ChevronDown: 'chevron-down',
  ChevronLeft: 'chevron-left',
  ChevronRight: 'chevron-right',
  AlertTriangle: 'alert-triangle',
  Info: 'info',
  CheckCircle2: 'check-circle-2',
  XCircle: 'x-circle',
  Play: 'play',
  Pause: 'pause',
  SkipBack: 'skip-back',
  SkipForward: 'skip-forward',
  Volume2: 'volume-2',
  Maximize: 'maximize',
  Star: 'star',
  UploadCloud: 'upload-cloud',
  Search: 'search',
  Bell: 'bell',
}

export const Check = (props: Omit<React.SVGProps<SVGSVGElement>, 'name'> & { size?: number }) => (
  <Icon name="check" {...props} />
)
export const X = (props: Omit<React.SVGProps<SVGSVGElement>, 'name'> & { size?: number }) => (
  <Icon name="x" {...props} />
)
export const ChevronDown = (
  props: Omit<React.SVGProps<SVGSVGElement>, 'name'> & { size?: number },
) => <Icon name="chevron-down" {...props} />
export const ChevronLeft = (
  props: Omit<React.SVGProps<SVGSVGElement>, 'name'> & { size?: number },
) => <Icon name="chevron-left" {...props} />
export const ChevronRight = (
  props: Omit<React.SVGProps<SVGSVGElement>, 'name'> & { size?: number },
) => <Icon name="chevron-right" {...props} />
export const AlertTriangle = (
  props: Omit<React.SVGProps<SVGSVGElement>, 'name'> & { size?: number },
) => <Icon name="alert-triangle" {...props} />
export const Info = (props: Omit<React.SVGProps<SVGSVGElement>, 'name'> & { size?: number }) => (
  <Icon name="info" {...props} />
)
export const CheckCircle2 = (
  props: Omit<React.SVGProps<SVGSVGElement>, 'name'> & { size?: number },
) => <Icon name="check-circle-2" {...props} />
export const XCircle = (props: Omit<React.SVGProps<SVGSVGElement>, 'name'> & { size?: number }) => (
  <Icon name="x-circle" {...props} />
)
export const Play = (props: Omit<React.SVGProps<SVGSVGElement>, 'name'> & { size?: number }) => (
  <Icon name="play" {...props} />
)
export const Pause = (props: Omit<React.SVGProps<SVGSVGElement>, 'name'> & { size?: number }) => (
  <Icon name="pause" {...props} />
)
export const SkipBack = (
  props: Omit<React.SVGProps<SVGSVGElement>, 'name'> & { size?: number },
) => <Icon name="skip-back" {...props} />
export const SkipForward = (
  props: Omit<React.SVGProps<SVGSVGElement>, 'name'> & { size?: number },
) => <Icon name="skip-forward" {...props} />
export const Volume2 = (props: Omit<React.SVGProps<SVGSVGElement>, 'name'> & { size?: number }) => (
  <Icon name="volume-2" {...props} />
)
export const Maximize = (
  props: Omit<React.SVGProps<SVGSVGElement>, 'name'> & { size?: number },
) => <Icon name="maximize" {...props} />
export const Star = (props: Omit<React.SVGProps<SVGSVGElement>, 'name'> & { size?: number }) => (
  <Icon name="star" {...props} />
)
export const UploadCloud = (
  props: Omit<React.SVGProps<SVGSVGElement>, 'name'> & { size?: number },
) => <Icon name="upload-cloud" {...props} />
export const Search = (props: Omit<React.SVGProps<SVGSVGElement>, 'name'> & { size?: number }) => (
  <Icon name="search" {...props} />
)
export const Bell = (props: Omit<React.SVGProps<SVGSVGElement>, 'name'> & { size?: number }) => (
  <Icon name="bell" {...props} />
)
