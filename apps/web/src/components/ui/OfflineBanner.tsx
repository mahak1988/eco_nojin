"use client";

import React, { useEffect, useState, type HTMLAttributes, forwardRef, type CSSProperties } from "react";

export interface OfflineBannerProps extends HTMLAttributes<HTMLDivElement> {
  message?: string;
  reconnectingMessage?: string;
}

const baseStyles: CSSProperties = {
  position: "fixed",
  top: 0,
  left: 0,
  right: 0,
  zIndex: 1000,
  padding: "var(--space-2) var(--space-4)",
  fontFamily: "var(--font-sans)",
  fontSize: "0.8125rem",
  fontWeight: 500,
  textAlign: "center",
  transform: "translateY(-100%)",
  transition: "transform var(--duration-240) var(--easing-ease-out-quart)",
};

const offlineStyles: CSSProperties = {
  background: "var(--color-copper)",
  color: "var(--color-paper)",
};

const reconnectingStyles: CSSProperties = {
  background: "var(--color-water)",
  color: "var(--color-paper)",
};

export const OfflineBanner = forwardRef<HTMLDivElement, OfflineBannerProps>(
  ({ message = "You are offline", reconnectingMessage = "Reconnecting...", className = "", style, ...props }, ref) => {
    const [isOnline, setIsOnline] = useState(true);
    const [wasOffline, setWasOffline] = useState(false);

    useEffect(() => {
      const handleOnline = () => {
        setIsOnline(true);
        if (wasOffline) {
          setWasOffline(false);
          setTimeout(() => setWasOffline(true), 2000);
        }
      };

      const handleOffline = () => {
        setIsOnline(false);
        setWasOffline(true);
      };

      setIsOnline(navigator.onLine);
      if (!navigator.onLine) setWasOffline(true);

      window.addEventListener("online", handleOnline);
      window.addEventListener("offline", handleOffline);

      return () => {
        window.removeEventListener("online", handleOnline);
        window.removeEventListener("offline", handleOffline);
      };
    }, [wasOffline]);

    if (isOnline && !wasOffline) return null;

    const isReconnecting = isOnline && wasOffline;
    const bannerMessage = isReconnecting ? reconnectingMessage : message;

    const combinedStyle: CSSProperties = {
      ...baseStyles,
      ...(isReconnecting ? reconnectingStyles : offlineStyles),
      transform: "translateY(0)",
      ...style,
    };

    return (
      <div
        ref={ref}
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className={className}
        style={combinedStyle}
        {...props}
      >
        <span aria-hidden="true">{isReconnecting ? "🔄" : "📡"}</span>
        <span>{bannerMessage}</span>
      </div>
    );
  }
);

OfflineBanner.displayName = "OfflineBanner";

export default OfflineBanner;