import staticIcon from '@/shared/assets/images/icons/magnifier-static.svg';
import hoverIcon from '@/shared/assets/images/icons/magnifier-hover.webp';
import { HoverIcon } from '@/shared/ui/HoverIcon';

type SearchIconProps = { width?: number; height?: number; className?: string };

export function SearchIcon(props: SearchIconProps) {
  return <HoverIcon staticIcon={staticIcon} hoverIcon={hoverIcon} replayIntervalMs={3000} {...props} />;
}
