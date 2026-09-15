// PWA Registration and Install Prompt

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

class PWAManager {
  private deferredPrompt: BeforeInstallPromptEvent | null = null;
  private isInstalled = false;
  private installButton: HTMLButtonElement | null = null;

  constructor() {
    this.init();
  }

  private async init() {
    if (!('serviceWorker' in navigator)) {
      console.log('[PWA] Service Worker not supported');
      return;
    }

    // Register service worker
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/',
      });
      console.log('[PWA] Service Worker registered:', registration.scope);

      // Check for updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              this.showUpdateAvailable();
            }
          });
        }
      });

      // Listen for controller change
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        window.location.reload();
      });
    } catch (error) {
      console.error('[PWA] Service Worker registration failed:', error);
    }

    // Handle install prompt
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      this.deferredPrompt = e as BeforeInstallPromptEvent;
      this.showInstallButton();
    });

    // Handle app installed
    window.addEventListener('appinstalled', () => {
      this.isInstalled = true;
      this.hideInstallButton();
      console.log('[PWA] App installed');
    });

    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      this.isInstalled = true;
    }

    // Listen for online/offline
    window.addEventListener('online', () => this.handleOnline());
    window.addEventListener('offline', () => this.handleOffline());
  }

  private showInstallButton() {
    if (this.isInstalled) return;

    // Create install button if not exists
    if (!this.installButton) {
      this.installButton = document.createElement('button');
      this.installButton.className = 'fixed bottom-4 left-4 z-50 glass glass-hover flex items-center gap-2 rounded-full bg-[var(--color-leaf-500)] px-4 py-2.5 text-xs font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.03] shadow-lg';
      this.installButton.innerHTML = `
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        <span>نصب اپلیکیشن</span>
      `;
      this.installButton.addEventListener('click', () => this.install());
      document.body.appendChild(this.installButton);

      // Auto-hide after 30 seconds
      setTimeout(() => this.hideInstallButton(), 30000);
    }
  }

  private hideInstallButton() {
    if (this.installButton) {
      this.installButton.remove();
      this.installButton = null;
    }
  }

  private async install() {
    if (!this.deferredPrompt) return;

    this.deferredPrompt.prompt();
    const { outcome } = await this.deferredPrompt.userChoice;

    if (outcome === 'accepted') {
      console.log('[PWA] User accepted install');
      this.isInstalled = true;
    } else {
      console.log('[PWA] User dismissed install');
    }

    this.deferredPrompt = null;
    this.hideInstallButton();
  }

  private showUpdateAvailable() {
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-4 right-4 z-50 glass flex items-center gap-3 rounded-2xl border border-[var(--color-leaf-500)]/40 bg-[var(--color-leaf-500)]/10 p-4 shadow-lg';
    toast.innerHTML = `
      <span class="text-lg">🔄</span>
      <div class="flex-1">
        <p class="font-bold text-[var(--color-night-100)]">نسخهٔ جدید در دسترس است</p>
        <p class="text-sm text-[var(--color-night-200)]/60">برای به‌روزرسانی صفحه را بازنشانی کنید</p>
      </div>
      <button class="shrink-0 rounded-full bg-[var(--color-leaf-500)] px-4 py-2 text-xs font-extrabold text-[var(--color-night-950)]" onclick="window.location.reload()">
        به‌روزرسانی
      </button>
    `;
    document.body.appendChild(toast);
  }

  private handleOnline() {
    console.log('[PWA] Back online');
    // Trigger background sync
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
      navigator.serviceWorker.ready.then((reg) => {
        (reg as any).sync.register('contact-form-sync');
      });
    }
  }

  private handleOffline() {
    console.log('[PWA] Gone offline');
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-4 right-4 z-50 glass flex items-center gap-3 rounded-2xl border border-[var(--color-aqua-500)]/40 bg-[var(--color-aqua-500)]/10 p-4 shadow-lg';
    toast.innerHTML = `
      <span class="text-lg">📡</span>
      <p class="font-bold text-[var(--color-aqua-300)]">شما آفلاین هستید</p>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
  }

  // Public API
  public async requestNotificationPermission(): Promise<NotificationPermission> {
    if (!('Notification' in window)) return 'denied';
    return Notification.requestPermission();
  }

  public async subscribeToPush(): Promise<PushSubscription | null> {
    const permission = await this.requestNotificationPermission();
    if (permission !== 'granted') return null;

    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: this.urlBase64ToUint8Array(import.meta.env.VITE_VAPID_PUBLIC_KEY || ''),
    });

    // Send subscription to server
    await fetch('/api/push/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(subscription),
    });

    return subscription;
  }

  private urlBase64ToUint8Array(base64String: string): BufferSource {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }
}

// Initialize PWA
let pwaManager: PWAManager | null = null;

if (typeof window !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      pwaManager = new PWAManager();
    });
  } else {
    pwaManager = new PWAManager();
  }
}

export { pwaManager };
export type { PWAManager };