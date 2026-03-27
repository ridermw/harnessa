const phases = [
  { key: 'planner', label: 'Planner', description: 'Analyzing code structure and creating review plan...' },
  { key: 'generator', label: 'Generator', description: 'Performing deep code analysis and finding issues...' },
  { key: 'evaluator', label: 'Evaluator', description: 'Scoring quality and generating final verdict...' },
];

export default function TrioProgress({ phaseStates }) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white flex items-center gap-2">
        <span className="text-harnessa-400">⚡</span> Trio Analysis in Progress
      </h3>
      <div className="space-y-3">
        {phases.map((phase, index) => {
          const state = phaseStates[phase.key] || 'pending';
          return (
            <div
              key={phase.key}
              className={`flex items-center gap-4 p-4 rounded-lg border transition-all duration-500 ${
                state === 'done'
                  ? 'bg-green-500/10 border-green-500/30'
                  : state === 'running'
                    ? 'bg-harnessa-500/10 border-harnessa-500/30 animate-pulse-glow'
                    : 'bg-gray-800/50 border-gray-700/50'
              }`}
            >
              <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-lg">
                {state === 'done' ? (
                  <span className="text-green-400 text-xl">✓</span>
                ) : state === 'running' ? (
                  <span className="animate-spin-slow inline-block text-harnessa-400">⟳</span>
                ) : (
                  <span className="text-gray-500">{index + 1}</span>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className={`font-semibold ${state === 'done' ? 'text-green-400' : state === 'running' ? 'text-harnessa-300' : 'text-gray-500'}`}>
                  {phase.label}
                </div>
                <div className="text-sm text-gray-400 truncate">
                  {state === 'done' ? 'Complete' : state === 'running' ? phase.description : 'Waiting...'}
                </div>
              </div>
              {state === 'running' && (
                <div className="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                  <div className="h-full bg-harnessa-500 rounded-full animate-pulse" style={{ width: '60%' }} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
