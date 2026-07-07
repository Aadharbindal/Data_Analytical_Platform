"use client";
import React from 'react';

const countries = [
  { name: 'United States', code: 'US', flag: '🇺🇸', percent: 85 },
  { name: 'Germany', code: 'DE', flag: '🇩🇪', percent: 70 },
  { name: 'Canada', code: 'CA', flag: '🇨🇦', percent: 60 },
  { name: 'Saudi Arabia', code: 'SA', flag: '🇸🇦', percent: 45 },
  { name: 'Australia', code: 'AU', flag: '🇦🇺', percent: 38 },
];

export const TopCountries: React.FC = () => {
  return (
    <div className="w-full bg-[#1a1a1a] rounded-2xl p-6 border border-[#2a2a2a] flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-sm font-semibold text-white">Top Countries</h3>
        <button className="bg-[#222] text-xs text-white px-2 py-1 rounded border border-[#333]">Sales v</button>
      </div>

      <div className="flex flex-col gap-4">
        {countries.map((c, i) => (
          <div key={i} className="flex items-center gap-3 text-xs">
            <span className="text-xl">{c.flag}</span>
            <div className="flex-1">
              <div className="flex justify-between mb-1">
                <span className="text-white font-medium">{c.name}</span>
                <span className="text-gray-400">{c.percent}%</span>
              </div>
              <div className="w-full h-1.5 bg-[#2a2a2a] rounded-full overflow-hidden">
                <div 
                  className="h-full bg-[#a3e635] rounded-full" 
                  style={{ width: `${c.percent}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
