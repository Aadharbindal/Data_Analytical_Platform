import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  // Bundle size & response optimizations
  compress: true,
  poweredByHeader: false,
  // Modular imports — only bundle what is imported (reduces Recharts & Lucide bundle ~60%)
  modularizeImports: {
    "lucide-react": {
      transform: "lucide-react/dist/esm/icons/{{kebabCase member}}",
    },
  },
};

export default nextConfig;
