/** @type {import('next').NextConfig} */
const nextConfig = {
  // Self-contained server bundle for the Docker image (docker compose up).
  output: "standalone",
  experimental: {
    typedRoutes: true
  }
};

export default nextConfig;
