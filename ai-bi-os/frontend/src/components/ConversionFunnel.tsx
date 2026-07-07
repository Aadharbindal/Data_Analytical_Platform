"use client";
import React from 'react';

export const ConversionFunnel: React.FC = () => {
  return (
    <div className="w-full bg-[#1a1a1a] rounded-2xl p-6 border border-[#2a2a2a] flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-sm font-semibold text-white">Conversion Funnel</h3>
        <button className="text-gray-400 hover:text-white">📅</button>
      </div>

      <div className="flex items-center gap-8">
        {/* Doughnut Chart Mock */}
        <div className="relative w-32 h-32 flex-shrink-0">
          <svg viewBox="0 0 36 36" className="w-full h-full transform -rotate-90">
            <path
              className="text-[#2a2a2a]"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="text-[#a3e635]"
              strokeDasharray="55.8, 100"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="currentColor"
              strokeWidth="4"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-white font-bold text-xl">55.8%</span>
            <span className="text-gray-500 text-[10px]">Overall</span>
          </div>
        </div>

        {/* Funnel Steps */}
        <div className="flex-1 flex flex-col justify-between h-32 py-2">
          
          <div className="flex flex-col gap-1">
            <div className="flex justify-between text-xs">
              <span className="text-white font-bold">120K <span className="text-gray-500 font-normal">Visitors</span></span>
              <span className="text-white">50%</span>
            </div>
            <div className="w-full h-2 bg-[#2a2a2a] rounded-full overflow-hidden">
              <div className="h-full bg-[#a3e635] w-[50%] rounded-full" />
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <div className="flex justify-between text-xs">
              <span className="text-white font-bold">42.5K <span className="text-gray-500 font-normal">Signups</span></span>
              <span className="text-white">50%</span>
            </div>
            <div className="w-full h-2 bg-[#2a2a2a] rounded-full overflow-hidden">
              <div className="h-full bg-[#a3e635] w-[35%] rounded-full" />
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <div className="flex justify-between text-xs">
              <span className="text-white font-bold">6.1K <span className="text-gray-500 font-normal">Purchase</span></span>
              <span className="text-white">50%</span>
            </div>
            <div className="w-full h-2 bg-[#2a2a2a] rounded-full overflow-hidden">
              <div className="h-full bg-[#a3e635] w-[5%] rounded-full" />
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};
