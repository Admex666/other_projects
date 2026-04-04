import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Prevent @imgly/background-removal and onnxruntime-web from being
  // bundled on the server side (they are browser/WASM-only)
  serverExternalPackages: ['@imgly/background-removal', 'onnxruntime-web'],

  // Empty turbopack config satisfies Next.js 16's requirement
  // (Turbopack is the default bundler in Next.js 16)
  turbopack: {},
};

export default nextConfig;
