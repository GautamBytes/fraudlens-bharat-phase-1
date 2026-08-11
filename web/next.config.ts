import type { NextConfig } from "next";

const isVercel = process.env.VERCEL === "1";

const nextConfig: NextConfig = {
  agentRules: false,
  output: isVercel ? undefined : "standalone",
  poweredByHeader: false,
  reactStrictMode: true,
};

export default nextConfig;
