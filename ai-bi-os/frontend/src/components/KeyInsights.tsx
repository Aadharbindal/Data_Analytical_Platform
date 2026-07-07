"use client";
import React from 'react';
import { Smartphone, Link } from 'lucide-react';

export const KeyInsights: React.FC<{ kpis?: any[] }> = ({ kpis = [] }) => {
  return (
    <div className="w-full bg-[#1a1a1a] rounded-2xl p-6 border border-[#2a2a2a] flex flex-col h-full overflow-y-auto">
      <h3 className="text-sm font-semibold text-white mb-4">Key Insights</h3>

      <div className="flex flex-col gap-4">
        {kpis.length === 0 ? (
          <p className="text-xs text-gray-400">Upload a dataset to see dynamic insights.</p>
        ) : (
          kpis.map((kpi, idx) => (
            <div key={idx} className="flex gap-4 items-center">
              <div className="w-10 h-10 rounded-xl bg-[#222] border border-[#333] flex items-center justify-center text-[#a3e635] flex-shrink-0 font-bold">
                {idx + 1}
              </div>
              <p className="text-sm text-gray-400 leading-relaxed">
                {kpi.title}: <span className="text-white font-bold">{kpi.value}</span>
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
