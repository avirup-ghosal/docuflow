import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        // redirects /api/auth/login -> http://127.0.0.1:80/auth/login
        destination: 'http://127.0.0.1:80/:path*', 
      },
    ];
  },
};

export default nextConfig;