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
