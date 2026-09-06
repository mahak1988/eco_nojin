import { useAuthStore } from '@eco/auth';
import { Avatar, Dropdown, DropdownContent, DropdownItem, DropdownSeparator, DropdownTrigger } from '@eco/ui';

export function UserMenu() {
  const session = useAuthStore((s) => s.session);
  const clear = useAuthStore((s) => s.clear);

  return (
    <Dropdown>
      <DropdownTrigger asChild>
        <button
          type="button"
          aria-label="User menu"
          className="flex items-center gap-2 rounded-md p-1 hover:bg-surface-muted"
        >
          <Avatar name={session?.user.full_name ?? session?.user.email ?? 'Guest'} size="sm" />
        </button>
      </DropdownTrigger>
      <DropdownContent align="end">
        <div className="px-2 py-2 text-xs text-ink-muted">
          <div className="font-medium text-ink">{session?.user.full_name ?? 'Guest'}</div>
          <div>{session?.user.email ?? '—'}</div>
          <div className="mt-1 inline-flex rounded bg-surface-muted px-1.5 py-0.5">
            {session?.user.role ?? 'guest'}
          </div>
        </div>
        <DropdownSeparator />
        <DropdownItem>Profile</DropdownItem>
        <DropdownItem>Settings</DropdownItem>
        <DropdownSeparator />
        <DropdownItem destructive onSelect={() => clear()}>
          Sign out
        </DropdownItem>
      </DropdownContent>
    </Dropdown>
  );
}