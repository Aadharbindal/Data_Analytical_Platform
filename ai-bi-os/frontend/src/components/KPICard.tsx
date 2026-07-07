import React from 'react';

interface KPICardProps {
  title: string;
  value: string;
  trend?: number;
}

export const KPICard: React.FC<KPICardProps> = ({ title, value, trend }) => {
  const isPositive = trend && trend >= 0;
  
  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col justify-between hover:shadow-md transition-shadow">
      <h3 className="text-gray-500 text-sm font-medium">{title}</h3>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-3xl font-semibold text-gray-900">{value}</span>
        {trend !== undefined && (
          <span className={`text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {isPositive ? '+' : ''}{trend}%
          </span>
        )}
      </div>
    </div>
  );
};
