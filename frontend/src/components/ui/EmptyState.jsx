export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {Icon && (
        <div className="w-14 h-14 rounded-2xl bg-surface-100 flex items-center justify-center mb-4">
          <Icon className="w-7 h-7 text-surface-400" />
        </div>
      )}
      <p className="text-sm font-medium text-surface-700">{title}</p>
      {description && <p className="text-xs text-surface-400 mt-1 max-w-xs">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
