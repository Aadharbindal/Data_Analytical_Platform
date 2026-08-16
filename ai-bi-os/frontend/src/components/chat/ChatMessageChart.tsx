"use client";

import React from "react";
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export interface ChatChartConfig {
  type: "bar" | "line" | "area";
  data: any[];
}

// Split out of ChatUI so Recharts can be loaded on demand. Most answers are
// text only, but importing the chart components at the top of ChatUI put the
// entire charting library in the bundle for every visit to the page —
// downloaded and parsed before the first message could render.
export default function ChatMessageChart({ config }: { config: ChatChartConfig }) {
  return (
    <div className="mt-3 h-64 w-full rounded-[20px] glass-panel p-4 shadow-sm">
      <ResponsiveContainer width="100%" height="100%">
        {config.type === "bar" ? (
          <BarChart data={config.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
            <XAxis
              dataKey="name"
              stroke="#80848E"
              fontSize={11}
              fontWeight={500}
              axisLine={false}
              tickLine={false}
              dy={10}
            />
            <YAxis stroke="#80848E" fontSize={11} fontWeight={500} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(19, 23, 34, 0.85)",
                backdropFilter: "blur(12px)",
                borderColor: "rgba(255,255,255,0.08)",
                borderRadius: "12px",
                padding: "8px 12px",
              }}
              itemStyle={{ color: "#fff", fontWeight: 600, fontSize: "13px" }}
            />
            <Bar dataKey="value" fill="#0070F3" radius={[4, 4, 0, 0]} />
          </BarChart>
        ) : config.type === "line" ? (
          <LineChart data={config.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis dataKey="name" stroke="#A0A4AE" fontSize={12} axisLine={false} tickLine={false} dy={10} />
            <YAxis stroke="#A0A4AE" fontSize={12} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#171B27",
                borderColor: "rgba(255,255,255,0.1)",
                borderRadius: "8px",
              }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#0070F3"
              strokeWidth={3}
              dot={{ r: 4, fill: "#0070F3", stroke: "#131722", strokeWidth: 2 }}
            />
          </LineChart>
        ) : (
          <AreaChart data={config.data}>
            <defs>
              <linearGradient id="colorArea" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0070F3" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#0070F3" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis dataKey="name" stroke="#A0A4AE" fontSize={12} axisLine={false} tickLine={false} dy={10} />
            <YAxis stroke="#A0A4AE" fontSize={12} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#171B27",
                borderColor: "rgba(255,255,255,0.1)",
                borderRadius: "8px",
              }}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke="#0070F3"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorArea)"
            />
          </AreaChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
