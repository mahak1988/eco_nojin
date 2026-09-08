import type { LucideIcon } from 'lucide-react';
import {
  Blocks,
  BookOpen,
  Bot,
  ChartLine,
  ClipboardList,
  CloudSun,
  Coins,
  Database,
  Droplets,
  FlaskConical,
  Globe,
  Layers,
  MessageSquare,
  Mic,
  MonitorSmartphone,
  Mountain,
  RefreshCcw,
  Route,
  Satellite,
  Server,
  Sprout,
  Store,
} from 'lucide-react';
import type { IconKey } from '../../content/site';

const iconMap: Record<IconKey, LucideIcon> = {
  satellite: Satellite,
  droplets: Droplets,
  sprout: Sprout,
  mountain: Mountain,
  blocks: Blocks,
  store: Store,
  globe: Globe,
  message: MessageSquare,
  sms: MonitorSmartphone,
  bot: Bot,
  mic: Mic,
  soil: Layers,
  climate: CloudSun,
  chart: ChartLine,
  book: BookOpen,
  clipboard: ClipboardList,
  sync: RefreshCcw,
  coins: Coins,
  flask: FlaskConical,
  workflow: Layers,
  server: Server,
  database: Database,
  route: Route,
};

interface IconProps {
  name: IconKey;
  className?: string;
  strokeWidth?: number;
  'aria-hidden'?: boolean | 'true' | 'false';
}

/** Maps a content-declared icon key to its lucide-react component. */
export default function Icon({ name, ...props }: IconProps) {
  const Component = iconMap[name];
  if (!Component) {
    throw new Error(`Unknown icon key: ${name}`);
  }
  return <Component {...props} />;
}
