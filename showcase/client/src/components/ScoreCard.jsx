export default function ScoreCard({ label, value, color }) {
  const colorClasses = {
    green: 'bg-green-500/20 text-green-400 border-green-500/30',
    yellow: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    red: 'bg-red-500/20 text-red-400 border-red-500/30',
    purple: 'bg-harnessa-500/20 text-harnessa-300 border-harnessa-500/30',
  };

  const scoreColor = color || (typeof value === 'number'
    ? value >= 7 ? 'green' : value >= 5 ? 'yellow' : 'red'
    : 'purple');

  return (
    <div className={`rounded-lg border p-4 ${colorClasses[scoreColor]}`}>
      <div className="text-sm font-medium opacity-80">{label}</div>
      <div className="text-2xl font-bold mt-1">
        {typeof value === 'number' ? value.toFixed(1) : value}
      </div>
    </div>
  );
}
