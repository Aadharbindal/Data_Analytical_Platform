// LazyCharts.tsx — Central export for all Recharts components
// This file is imported via next/dynamic to ensure Recharts is only bundled
// when it is actually needed, keeping the initial JS payload small.
export {
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  ComposedChart,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
  ReferenceDot,
} from "recharts";
