import { ImageResponse } from "next/og";

// Generated rather than shipped as a static PNG, so the card always matches
// the app's own palette and mark instead of drifting from it over time.
export const alt = "Numerate — natural language in, verified numbers out";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

// One settled frame of the animated logo: three isometric plates, the same
// 45deg rotation flattened to 0.42 on Y, in the same three blues.
function Plate({ color, offsetY, filled }: { color: string; offsetY: number; filled: boolean }) {
  return (
    <div
      style={{
        position: "absolute",
        display: "flex",
        width: 132,
        height: 132,
        // Centred in the 240px circle: left/top of 54 puts the box centre on
        // 120, then offsetY spreads the three plates around it. Rotating 45deg
        // makes the visual height 132*sqrt(2)*0.42 ~= 78, so a +/-34 spread
        // keeps the whole stack inside the circle instead of spilling past it.
        top: 54 + offsetY,
        left: 54,
        borderRadius: 10,
        transform: "scaleY(0.42) rotate(45deg)",
        ...(filled
          ? { background: color, boxShadow: `0 0 60px ${color}` }
          : { border: `8px solid ${color}` }),
      }}
    />
  );
}

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "0 90px",
          background: "#0B0D12",
          backgroundImage:
            "radial-gradient(circle at 22% 34%, rgba(59,130,246,0.30) 0%, rgba(11,13,18,0) 55%)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center" }}>
          {/* Logo mark */}
          <div
            style={{
              position: "relative",
              display: "flex",
              width: 240,
              height: 240,
              borderRadius: 120,
              background:
                "radial-gradient(circle at 50% 45%, #141c2e 0%, #0a0e1a 75%)",
              border: "2px solid rgba(255,255,255,0.08)",
              boxShadow: "0 0 90px rgba(59,130,246,0.42)",
            }}
          >
            <Plate color="#1e40af" offsetY={34} filled={false} />
            <Plate color="#3b82f6" offsetY={0} filled={false} />
            <Plate color="#6b9cf6" offsetY={-34} filled />
          </div>

          <div style={{ display: "flex", flexDirection: "column", marginLeft: 68 }}>
            <div
              style={{
                display: "flex",
                fontSize: 104,
                fontWeight: 700,
                color: "#FFFFFF",
                letterSpacing: -3,
                lineHeight: 1.05,
              }}
            >
              Numerate
            </div>
            <div
              style={{
                display: "flex",
                marginTop: 18,
                fontSize: 36,
                color: "#A0A4AE",
                letterSpacing: -0.5,
              }}
            >
              Smart Analytics. Better Decisions.
            </div>
          </div>
        </div>

        <div
          style={{
            display: "flex",
            marginTop: 64,
            paddingTop: 34,
            borderTop: "2px solid rgba(255,255,255,0.07)",
            fontSize: 30,
            color: "#6b9cf6",
          }}
        >
          Ask in plain English. Every number computed, then verified.
        </div>
      </div>
    ),
    size
  );
}
