/** @type {import('next').NextConfig} */
const isExport = process.env.NEXT_OUTPUT === "export";

const nextConfig = {
  reactStrictMode: true,
  images: { unoptimized: true },
  ...(isExport
    ? { output: "export", trailingSlash: true }
    : {
        async rewrites() {
          const target = process.env.API_PROXY_TARGET || "http://127.0.0.1:8000";
          return [
            {
              source: "/api/:path*",
              destination: `${target}/api/:path*`,
            },
          ];
        },
      }),
};

module.exports = nextConfig;
