const backendUrl = process.env.BACKEND_URL ?? 'http://localhost:8000';

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Минимальный self-contained образ: .next/standalone + server.js вместо
  // полного node_modules с `next start`.
  // ВАЖНО: вместе с этим rewrites ниже вычисляются на СБОРКЕ, а не на
  // рантайме, поэтому BACKEND_URL надо передавать как build-arg (см. frontend/Dockerfile).
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
