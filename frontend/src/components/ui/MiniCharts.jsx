/**
 * MiniCharts — Lightweight reusable chart components for dashboard visualizations.
 * Uses recharts under the hood but exposes simple, role-specific interfaces.
 */
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";

const COLORS = {
  blue: "#2563eb",
  emerald: "#059669",
  amber: "#d97706",
  red: "#dc2626",
  purple: "#7c3aed",
  cyan: "#0891b2",
  slate: "#64748b",
};

function MiniTooltip({ active, payload, label, unit }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-900 text-white text-xs px-3 py-2 rounded-lg shadow-lg">
      <p className="text-slate-400 mb-0.5">{label}</p>
      {payload.map((p, i) => (
        <p key={i} className="font-semibold">
          {p.name}: {p.value}{unit || ""}
        </p>
      ))}
    </div>
  );
}

/**
 * SparkLine — Tiny inline trend line (no axes, just the shape)
 */
export function SparkLine({ data, dataKey = "value", color = "blue", height = 40, className = "" }) {
  return (
    <div className={`w-full ${className}`} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: 4 }}>
          <Line
            type="monotone"
            dataKey={dataKey}
            stroke={COLORS[color] || color}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 3, fill: COLORS[color] || color }}
          />
          <Tooltip content={<MiniTooltip />} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * VitalsTrendChart — Shows vitals over time with reference bands
 */
export function VitalsTrendChart({ data, dataKey = "value", name = "Value", color = "blue", unit = "", height = 120, refMin, refMax }) {
  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
          <defs>
            <linearGradient id={`grad-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={COLORS[color] || color} stopOpacity={0.2} />
              <stop offset="95%" stopColor={COLORS[color] || color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="time" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} width={30} domain={refMin && refMax ? [refMin - 5, refMax + 5] : ["auto", "auto"]} />
          <Tooltip content={<MiniTooltip unit={unit} />} />
          <Area
            type="monotone"
            dataKey={dataKey}
            name={name}
            stroke={COLORS[color] || color}
            strokeWidth={2}
            fill={`url(#grad-${dataKey})`}
            activeDot={{ r: 4, fill: COLORS[color] || color }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * ActivityBar — Mini bar chart for daily/weekly activity
 */
export function ActivityBar({ data, dataKey = "count", color = "blue", height = 80 }) {
  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: 4 }}>
          <Bar dataKey={dataKey} fill={COLORS[color] || color} radius={[3, 3, 0, 0]} opacity={0.8} />
          <Tooltip content={<MiniTooltip />} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * MultiLineChart — Multiple metrics on one chart (e.g., systolic + diastolic BP)
 */
export function MultiLineChart({ data, lines = [], height = 140 }) {
  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="time" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} width={30} />
          <Tooltip content={<MiniTooltip />} />
          {lines.map(({ dataKey, name, color }) => (
            <Line
              key={dataKey}
              type="monotone"
              dataKey={dataKey}
              name={name}
              stroke={COLORS[color] || color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 3 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * StatWithSparkline — A stat number with an inline sparkline below it
 */
export function StatWithSparkline({ label, value, unit, data, dataKey = "value", color = "blue", trend }) {
  const trendColor = trend > 0 ? "text-emerald-600" : trend < 0 ? "text-red-600" : "text-slate-400";
  const trendIcon = trend > 0 ? "↑" : trend < 0 ? "↓" : "→";

  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-1">
        <p className="text-xs font-semibold text-slate-500">{label}</p>
        {trend !== undefined && (
          <span className={`text-xs font-bold ${trendColor}`}>{trendIcon} {Math.abs(trend)}%</span>
        )}
      </div>
      <p className="text-2xl font-bold text-slate-900">{value}<span className="text-sm text-slate-400 ml-1">{unit}</span></p>
      {data?.length > 1 && <SparkLine data={data} dataKey={dataKey} color={color} height={32} className="mt-2" />}
    </div>
  );
}
