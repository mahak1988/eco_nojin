"use client";

import React, {
  useEffect,
  useRef,
  useState,
  useCallback,
  type ReactNode,
  type ChangeEvent,
  forwardRef,
  type CSSProperties,
} from "react";
import { createPortal } from "react-dom";

export interface CommandPaletteItem {
  label: string;
  description?: string;
  action: () => void;
  shortcut?: string;
  icon?: ReactNode;
}

export interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  items: CommandPaletteItem[];
  placeholder?: string;
  portalTarget?: HTMLElement | null;
  className?: string;
  style?: CSSProperties;
}

const overlayStyles: CSSProperties = {
  position: "fixed",
  inset: 0,
  backgroundColor: "color-mix(in oklch, var(--color-ink) 40%, transparent)",
  backdropFilter: "blur(2px)",
  WebkitBackdropFilter: "blur(2px)",
  zIndex: 99,
  animation: "fadeIn var(--duration-120) var(--easing-ease-out-quart)",
};

const paletteStyles: CSSProperties = {
  position: "fixed",
  top: "15%",
  left: "50%",
  transform: "translateX(-50%)",
  width: "min(640px, calc(100vw - var(--space-8)))",
  backgroundColor: "var(--color-surface)",
  border: "1px solid var(--color-line)",
  borderRadius: "var(--radius-16)",
  boxShadow: "var(--shadow-pop)",
  overflow: "hidden",
  zIndex: 100,
  animation: "slideDown var(--duration-240) var(--easing-ease-out-quart)",
};

const inputStyles: CSSProperties = {
  width: "100%",
  padding: "var(--space-4)",
  fontFamily: "var(--font-sans)",
  fontSize: "1rem",
  color: "var(--color-ink)",
  background: "var(--color-surface-2)",
  border: "none",
  borderBottom: "1px solid var(--color-line)",
  outline: "none",
};

const listStyles: CSSProperties = {
  maxHeight: "400px",
  overflowY: "auto",
  padding: "var(--space-2)",
  margin: 0,
  listStyle: "none",
};

const itemStyles: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "var(--space-3)",
  padding: "var(--space-3) var(--space-4)",
  borderRadius: "var(--radius-8)",
  cursor: "pointer",
  transition: "background-color var(--duration-120) var(--easing-ease-out-quart)",
};

const itemHoverStyles: CSSProperties = {
  backgroundColor: "var(--color-surface-2)",
};

const keyframes = `
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  @keyframes slideDown {
    from { opacity: 0; transform: translateX(-50%) translateY(-10px); }
    to { opacity: 1; transform: translateX(-50%) translateY(0); }
  }
`;

export const CommandPalette = forwardRef<HTMLDivElement, CommandPaletteProps>(
  ({ open, onOpenChange, items, placeholder = "Search commands...", portalTarget, className = "", style, ...props }, ref) => {
    const [query, setQuery] = useState("");
    const [selectedIndex, setSelectedIndex] = useState(0);
    const inputRef = useRef<HTMLInputElement>(null);
    const itemRefs = useRef<(HTMLLIElement | null)[]>([]);

    const filteredItems = items.filter(
      (item) =>
        item.label.toLowerCase().includes(query.toLowerCase()) ||
        item.description?.toLowerCase().includes(query.toLowerCase()) ||
        item.shortcut?.toLowerCase().includes(query.toLowerCase())
    );

    const handleKeyDown = useCallback(
      (event: React.KeyboardEvent<HTMLInputElement>) => {
        switch (event.key) {
          case "Escape":
            event.preventDefault();
            onOpenChange(false);
            setQuery("");
            setSelectedIndex(0);
            break;
          case "ArrowDown":
            event.preventDefault();
            setSelectedIndex((prev) => Math.min(prev + 1, filteredItems.length - 1));
            break;
          case "ArrowUp":
            event.preventDefault();
            setSelectedIndex((prev) => Math.max(prev - 1, 0));
            break;
          case "Enter":
            event.preventDefault();
            if (filteredItems[selectedIndex]) {
              filteredItems[selectedIndex].action();
              onOpenChange(false);
              setQuery("");
              setSelectedIndex(0);
            }
            break;
        }
      },
      [filteredItems, onOpenChange, selectedIndex]
    );

    const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
      setQuery(event.target.value);
      setSelectedIndex(0);
    };

    useEffect(() => {
      if (open) {
        setQuery("");
        setSelectedIndex(0);
        setTimeout(() => inputRef.current?.focus(), 0);
      }
    }, [open]);

    useEffect(() => {
      if (open) {
        const handleGlobalKeyDown = (event: globalThis.KeyboardEvent) => {
          if ((event.metaKey || event.ctrlKey) && event.key === "k") {
            event.preventDefault();
            onOpenChange(false);
            setQuery("");
            setSelectedIndex(0);
          }
        };
        document.addEventListener("keydown", handleGlobalKeyDown);
        return () => document.removeEventListener("keydown", handleGlobalKeyDown);
      }
    }, [open, onOpenChange]);

    useEffect(() => {
      const selectedItem = itemRefs.current[selectedIndex];
      selectedItem?.scrollIntoView({ block: "nearest" });
    }, [selectedIndex]);

    const content = (
      <>
        <style dangerouslySetInnerHTML={{ __html: keyframes }} />
        <div
          style={overlayStyles}
          onClick={() => { onOpenChange(false); setQuery(""); setSelectedIndex(0); }}
          aria-hidden="true"
        />
        <div
          ref={ref}
          role="dialog"
          aria-label="Command palette"
          style={{
            ...style,
            ...paletteStyles,
          }}
          className={className}
          {...props}
        >
          <input
            ref={inputRef}
            type="search"
            placeholder={placeholder}
            value={query}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            style={inputStyles}
            autoComplete="off"
            aria-label="Search commands"
            aria-controls="command-palette-list"
            aria-activedescendant={filteredItems[selectedIndex] ? `cmd-item-${selectedIndex}` : undefined}
          />
          <ul id="command-palette-list" role="listbox" style={listStyles}>
            {filteredItems.length === 0 ? (
              <li
                style={{
                  ...itemStyles,
                  justifyContent: "center",
                  color: "var(--color-ink-soft)",
                  cursor: "default",
                }}
                role="option"
                aria-disabled="true"
              >
                No commands found
              </li>
            ) : (
              filteredItems.map((item, index) => (
                <li
                  key={item.label}
                  ref={(el) => { itemRefs.current[index] = el; }}
                  id={`cmd-item-${index}`}
                  role="option"
                  aria-selected={index === selectedIndex}
                  style={{
                    ...itemStyles,
                    ...(index === selectedIndex ? itemHoverStyles : {}),
                  }}
                  onClick={() => {
                    item.action();
                    onOpenChange(false);
                    setQuery("");
                    setSelectedIndex(0);
                  }}
                  onMouseEnter={() => setSelectedIndex(index)}
                >
                  {item.icon && <span style={{ fontSize: "1.25rem", lineHeight: 1 }}>{item.icon}</span>}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontFamily: "var(--font-sans)", fontSize: "0.875rem", fontWeight: 500, color: "var(--color-ink)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                      {item.label}
                    </div>
                    {item.description && (
                      <div style={{ fontFamily: "var(--font-sans)", fontSize: "0.75rem", color: "var(--color-ink-soft)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {item.description}
                      </div>
                    )}
                  </div>
                  {item.shortcut && (
                    <kbd style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.6875rem",
                      color: "var(--color-ink-faint)",
                      background: "var(--color-surface-2)",
                      padding: "var(--space-1) var(--space-2)",
                      borderRadius: "var(--radius-2)",
                      border: "1px solid var(--color-line)",
                    }}>
                      {item.shortcut}
                    </kbd>
                  )}
                </li>
              ))
            )}
          </ul>
        </div>
      </>
    );

    if (!open) return null;

    const target = portalTarget ?? document.body;
    return createPortal(content, target);
  }
);

CommandPalette.displayName = "CommandPalette";

export default CommandPalette;