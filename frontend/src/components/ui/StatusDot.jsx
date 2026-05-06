const colors = {
  approved: "bg-emerald-500",
  pending:  "bg-amber-400",
  denied:   "bg-red-500",
  revoked:  "bg-surface-400",
  expired:  "bg-surface-300",
  success:  "bg-emerald-500",
  error:    "bg-red-500",
  healthy:  "bg-emerald-500",
  degraded: "bg-amber-400",
};

export default function StatusDot({ status, pulse = false }) {
  const color = colors[status] || "bg-surface-400";
  return (
    <span className="relative flex h-2 w-2">
      {pulse && <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${color} opacity-75`} />}
      <span className={`relative inline-flex rounded-full h-2 w-2 ${color}`} />
    </span>
  );
}
