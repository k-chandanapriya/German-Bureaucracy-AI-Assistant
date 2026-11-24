import type { NextConfig } from "next";

// GITHUB_PAGES=true builds a static site for GitHub Pages, served from
// https://<user>.github.io/<repo>/ (see .github/workflows/pages.yml).
const pages = process.env.GITHUB_PAGES === "true";
const repo = "/German-Bureaucracy-AI-Assistant";

const nextConfig: NextConfig = {
  // Partial prerendering needs a Next.js server, so it's off for the static build.
  cacheComponents: !pages,
  partialPrefetching: !pages,
  ...(pages && {
    output: "export",
    basePath: repo,
    trailingSlash: true,
    images: { unoptimized: true },
  }),
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
