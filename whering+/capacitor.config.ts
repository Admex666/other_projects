import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'app.digital.atelier',
  appName: 'Digital Atelier',
  webDir: 'public',
  server: {
    url: 'https://wheringplus.vercel.app/',
    cleartext: true
  }
};

export default config;
