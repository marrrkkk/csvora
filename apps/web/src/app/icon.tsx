import type { MetadataRoute } from "next";

export default function Icon(): MetadataRoute.Icon {
  return {
    type: "image/svg+xml",
    body: `
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#111827"/>
  <path d="M18 20h28v6H18z" fill="#ffffff" opacity="0.95"/>
  <path d="M18 30h20v6H18z" fill="#ffffff" opacity="0.85"/>
  <path d="M18 40h26v6H18z" fill="#ffffff" opacity="0.75"/>
  <path d="M44 30l4 3-4 3" fill="none" stroke="#22c55e" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
    `.trim(),
  };
}

