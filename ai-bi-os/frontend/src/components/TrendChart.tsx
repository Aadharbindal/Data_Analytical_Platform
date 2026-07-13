"use client";
import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface ChartDataPoint {
  name: string;
  value: number;
}

interface TrendChartProps {
  data: ChartDataPoint[];
  title?: string;
}

export const TrendChart: React.FC<TrendChartProps> = ({ data, title = "Revenue Analytics" }) => {
  if (!data || data.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center text-gray-500">
        No chart data available. Upload a dataset.
      </div>
    );
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#1e1e1e] border border-[#333] p-3 rounded-lg shadow-xl">
          <p className="text-gray-400 text-xs mb-1">{label}</p>
          <p className="text-white font-bold text-lg">₹{payload[0].value.toLocaleString()}</p>
          <p className="text-[#a3e635] text-xs font-medium mt-1">▲ +12.5% vs last week</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-full flex flex-col bg-[#1a1a1a] rounded-2xl p-6 border border-[#2a2a2a]">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white mb-1">{title}</h3>
          <div className="flex items-center gap-3">
            <span className="text-2xl font-bold text-white">
              ₹{data[data.length - 1]?.value.toLocaleString() || '130,800'}
            </span>
            <span className="text-[#a3e635] text-sm font-medium bg-[#1e2a14] px-2 py-0.5 rounded-full">
              ▲ +12.5%
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="bg-[#222] text-xs text-white px-3 py-1.5 rounded-md border border-[#333]">All Channel</button>
          <button className="bg-[#222] text-xs text-white px-3 py-1.5 rounded-md border border-[#333]">Sales Volume</button>
        </div>
      </div>
      
      <div className="flex-1 min-h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="neonGreen" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#a3e635" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#a3e635" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#2a2a2a" />
            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#666', fontSize: 11}} dy={10} />
            <YAxis axisLine={false} tickLine={false} tick={{fill: '#666', fontSize: 11}} tickFormatter={(val) => `₹${val/1000}K`} />
            <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#555', strokeWidth: 1, strokeDasharray: '4 4' }} />
            <Area type="monotone" dataKey="value" stroke="#a3e635" strokeWidth={3} fillOpacity={1} fill="url(#neonGreen)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
