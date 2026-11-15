import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    serverActions: {
      allowedOrigins: [
        '*.trycloudflare.com',
        'trycloudflare.com',
        'loca.lt',
        '*.loca.lt',
        'localhost:3000',
        'localhost:3001',
        '192.168.0.112:3000',
        '192.168.0.237:3000',
        '192.168.0.237:3001',
      ],
    },
  },
};

export default nextConfig;
