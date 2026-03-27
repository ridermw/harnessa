export default function BugList({ bugs }) {
  if (!bugs || bugs.length === 0) {
    return (
      <div className="text-center py-6 text-gray-500">
        <span className="text-2xl">🎉</span>
        <p className="mt-2">No bugs found!</p>
      </div>
    );
  }

  const severityColors = {
    critical: 'bg-red-500/20 text-red-400 border-red-500/30',
    high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    low: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  };

  const severityIcons = {
    critical: '🔴',
    high: '🟠',
    medium: '🟡',
    low: '🔵',
  };

  return (
    <div className="space-y-3">
      {bugs.map((bug, i) => (
        <div
          key={bug.id || i}
          className={`rounded-lg border p-4 ${severityColors[bug.severity] || severityColors.low}`}
        >
          <div className="flex items-center gap-2 mb-2">
            <span>{severityIcons[bug.severity] || '🔵'}</span>
            <span className="font-semibold text-sm uppercase">{bug.severity}</span>
            <span className="text-xs opacity-70">— {bug.type?.replace(/-/g, ' ')}</span>
            {bug.line && (
              <span className="ml-auto text-xs opacity-60">Line {bug.line}</span>
            )}
          </div>
          <p className="text-sm">{bug.description}</p>
          {bug.suggestion && (
            <p className="text-xs mt-2 opacity-70">
              💡 {bug.suggestion}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
