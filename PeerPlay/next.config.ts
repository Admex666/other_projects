import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    serverActions: {
      allowedOrigins: [
        'loca.lt',
        '*.loca.lt',
        'localhost:3000',
        '192.168.0.112:3000',
      ],
    },
  },
};

export default nextConfig;
