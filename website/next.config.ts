import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // This enables the ability to read files from outside the website directory
  outputFileTracingRoot: process.env.NODE_ENV === 'development' 
    ? process.cwd() 
    : process.cwd() + '/..',
  
  // Other configuration options can go here
  reactStrictMode: true,
  images: {
    domains: ['cdn.example.com'], // Add any image domains if needed
  },
};

export default nextConfig;