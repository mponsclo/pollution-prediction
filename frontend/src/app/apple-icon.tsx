import { ImageResponse } from "next/og";

export const size = { width: 180, height: 180 };
export const contentType = "image/png";

export default function AppleIcon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          background: "#0a0a0a",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <svg width="180" height="180" viewBox="0 0 180 180" fill="none">
          <path
            d="M20 60 Q 55 30, 90 60 T 160 60"
            stroke="#22d3ee"
            strokeWidth="12"
            strokeLinecap="round"
            fill="none"
          />
          <path
            d="M20 90 Q 55 60, 90 90 T 160 90"
            stroke="#0ea5bf"
            strokeWidth="12"
            strokeLinecap="round"
            fill="none"
          />
          <path
            d="M20 120 Q 55 90, 90 120 T 160 120"
            stroke="#0891b2"
            strokeWidth="12"
            strokeLinecap="round"
            fill="none"
          />
        </svg>
      </div>
    ),
    { ...size },
  );
}
