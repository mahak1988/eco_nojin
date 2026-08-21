import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.econojin.app',
  appName: 'Eco Nojin',
  webDir: 'out',
  server: {
    // In production, bundle the web assets
    androidScheme: 'https',
  },
  plugins: {
    Geolocation: {
      // Request permissions at runtime
    },
    Camera: {
      // Allow camera access for field observations
    },
    LocalNotifications: {
      smallIcon: 'ic_stat_icon_config_sample',
      iconColor: '#15803d',
    },
    SplashScreen: {
      launchAutoHide: true,
      launchShowDuration: 2000,
      backgroundColor: '#15803d',
      showSpinner: true,
      spinnerColor: '#ffffff',
    },
  },
  android: {
    allowMixedContent: true,
    captureInput: true,
    webContentsDebuggingEnabled: false,
  },
};

export default config;
