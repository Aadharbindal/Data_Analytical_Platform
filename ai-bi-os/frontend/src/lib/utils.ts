import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatIndianNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return "N/A";
  
  const absValue = Math.abs(value);
  const sign = value < 0 ? "-" : "";
  
  if (absValue >= 1_00_00_000) return `${sign}${parseFloat((absValue / 1_00_00_000).toFixed(2))}Cr`;
  if (absValue >= 1_00_000) return `${sign}${parseFloat((absValue / 1_00_000).toFixed(2))}L`;
  if (absValue >= 1_000) return `${sign}${parseFloat((absValue / 1_000).toFixed(1))}K`;
  
  return `${sign}${absValue.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
}

export const formatNumber = formatIndianNumber;

export function formatIndianCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) return "N/A";
  
  const absValue = Math.abs(value);
  const sign = value < 0 ? "-" : "";
  
  if (absValue >= 1_00_00_000) return `${sign}₹${parseFloat((absValue / 1_00_00_000).toFixed(2))}Cr`;
  if (absValue >= 1_00_000) return `${sign}₹${parseFloat((absValue / 1_00_000).toFixed(2))}L`;
  if (absValue >= 1_000) return `${sign}₹${parseFloat((absValue / 1_000).toFixed(1))}K`;
  
  return `${sign}₹${absValue.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
}

/** Formats a KPI's value the way the dashboard metric cards do. Shared so the
 *  Customize panel shows exactly the same number the card it controls shows,
 *  instead of the two drifting apart. */
export function formatKpiValue(value: number, type?: string): string {
  const isNegative = value < 0;
  const absValue = Math.abs(value);
  const sign = isNegative ? "-" : "";

  if (type === "count" || type === "generic") {
    if (absValue >= 1_000_000) return `${sign}${(absValue / 1_000_000).toFixed(1)}M`;
    if (absValue >= 1_000) return `${sign}${(absValue / 1_000).toFixed(1)}K`;
    return `${sign}${absValue}`;
  }
  if (type === "percent") {
    return `${sign}${absValue.toFixed(1)}%`;
  }

  // Indian Rupee formatting: Cr / L / K
  if (absValue >= 1_00_00_000) return `${sign}₹${(absValue / 1_00_00_000).toFixed(2)}Cr`;
  if (absValue >= 1_00_000) return `${sign}₹${(absValue / 1_00_000).toFixed(2)}L`;
  if (absValue >= 1_000) return `${sign}₹${(absValue / 1_000).toFixed(1)}K`;
  return `${sign}₹${absValue.toLocaleString("en-IN")}`;
}

export function formatPercent(value: number | null | undefined, includeSign = false): string {
  if (value === null || value === undefined) return "N/A";
  
  const formatted = new Intl.NumberFormat('en-IN', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value / 100);
  
  if (includeSign && value > 0) {
    return `+${formatted}`;
  }
  return formatted;
}

export function formatDecimal(value: number | null | undefined, fractionDigits = 3): string {
  if (value === null || value === undefined) return "N/A";
  
  return new Intl.NumberFormat('en-IN', {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits
  }).format(value);
}
