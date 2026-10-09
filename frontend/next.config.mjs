/** @type {import('next').NextConfig} */
const nextConfig = {
  ...(process.env.DOCKER_BUILD === "1" ? { output: "standalone" } : {}),
  reactStrictMode: true,
};
export default nextConfig;
