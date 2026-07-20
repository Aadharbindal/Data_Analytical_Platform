import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  // Bundle size & response optimizations
  compress: true,
  poweredByHeader: false,
  experimental: {
    // Tree-shake heavy packages — pulls only used exports into the bundle
    // Replaces the old modularizeImports approach with Next.js built-in optimization
    optimizePackageImports: [
      "recharts",
      "framer-motion",
      "@radix-ui/react-icons",
      "lucide-react",
    ],
  },
};

export default nextConfig;
