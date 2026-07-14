"use client";
import React from 'react';
import { AreaChart, Area, ResponsiveContainer } from 'recharts';
import { ArrowUpRight } from 'lucide-react';

export const TrafficChart: React.FC = () => {
  const data = [
    { name: 'Mon', value: 4000 },
    { name: 'Tue', value: 3000 },
    { name: 'Wed', value: 5000 },
    { name: 'Thu', value: 8000 },
    { name: 'Fri', value: 6000 },
    { name: 'Sat', value: 9000 },
    { name: 'Sun', value: 11000 },
  ];

  return (
    <div className="w-full h-full bg-[#1a1a1a] rounded-2xl p-6 border border-[#2a2a2a] flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-sm font-semibold text-white">Traffic Source</h3>
        <button className="bg-[#222] text-xs text-white px-2 py-1 rounded border border-[#333]">Revenue v</button>
      </div>
      
      <div className="flex-1 min-h-[100px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="neonGreenMini" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#a3e635" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#a3e635" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <Area type="monotone" dataKey="value" stroke="#a3e635" strokeWidth={2} fillOpacity={1} fill="url(#neonGreenMini)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4">
        <div className="flex justify-between items-end mb-6">
          <div className="flex flex-col gap-1">
            <h3 className="text-gray-400 font-medium">Total Volume</h3>
            <span className="text-2xl font-bold text-white">₹130,800</span>
          </div>
          <div className="bg-[#1e2a14] px-2 py-1 rounded flex items-center gap-1">
            <ArrowUpRight className="w-3 h-3 text-[#a3e635]" />
            <span className="text-[#a3e635] text-xs font-semibold">12.5%</span>
          </div>
        </div>
        <p className="text-[10px] text-gray-500 mt-2">Driven mainly by Paid traffic (+18%)</p>
      </div>
    </div>
  );
};
