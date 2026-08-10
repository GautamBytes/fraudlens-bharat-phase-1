import type { NextConfig } from "next";

const isVercel = process.env.VERCEL === "1";

const nextConfig: NextConfig = {
  output: isVercel ? undefined : "standalone",
  poweredByHeader: false,
  reactStrictMode: true,
};

export default nextConfig;
