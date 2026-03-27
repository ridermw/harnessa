import { useEffect, useState } from 'react';

export default function Analytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/analytics')
      .then((r) => r.json())
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin-slow text-4xl text-harnessa-400">⟳</div>
      </div>
    );
  }

  const maxScore = 10;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white">Analytics</h1>
        <p className="text-gray-400 mt-1">Quality trends and review insights</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="text-sm text-gray-400">Total Reviews</div>
          <div className="text-3xl font-bold text-white mt-1">{data?.totalReviews ?? 0}</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="text-sm text-gray-400">Average Score</div>
          <div className="text-3xl font-bold text-harnessa-400 mt-1">
            {(data?.averageScore ?? 0).toFixed(1)}
          </div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="text-sm text-gray-400">Pass Rate</div>
          <div className="text-3xl font-bold text-green-400 mt-1">{data?.passRate ?? 0}%</div>
        </div>
      </div>

      {/* Score Chart */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-6">Recent Review Scores</h2>
        {(!data?.recentScores || data.recentScores.length === 0) ? (
          <p className="text-gray-500 text-center py-8">No completed reviews yet. Submit code for analysis to see trends.</p>
        ) : (
          <div className="flex items-end gap-2 h-48">
            {data.recentScores.slice().reverse().map((review, i) => {
              const height = (review.overall_score / maxScore) * 100;
              const color = review.overall_score >= 7
                ? 'bg-green-500'
                : review.overall_score >= 5
                  ? 'bg-yellow-500'
                  : 'bg-red-500';
              return (
                <div key={review.id || i} className="flex-1 flex flex-col items-center gap-1">
                  <span className="text-xs text-gray-400">{review.overall_score?.toFixed(1)}</span>
                  <div
                    className={`w-full rounded-t-md ${color} transition-all duration-500`}
                    style={{ height: `${height}%`, minHeight: '4px' }}
                    title={`${review.language} — ${review.overall_score}/10`}
                  />
                  <span className="text-xs text-gray-600 truncate w-full text-center">
                    {review.language?.substring(0, 4)}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* By Language */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Reviews by Language</h2>
        {(!data?.byLanguage || data.byLanguage.length === 0) ? (
          <p className="text-gray-500 text-center py-4">No data yet.</p>
        ) : (
          <div className="space-y-3">
            {data.byLanguage.map((lang) => (
              <div key={lang.language} className="flex items-center gap-4">
                <span className="text-sm text-gray-300 w-24">{lang.language}</span>
                <div className="flex-1 bg-gray-800 rounded-full h-3 overflow-hidden">
                  <div
                    className="bg-harnessa-500 h-full rounded-full transition-all"
                    style={{ width: `${(lang.count / (data?.totalReviews || 1)) * 100}%` }}
                  />
                </div>
                <span className="text-sm text-gray-400 w-20 text-right">
                  {lang.count} review{lang.count !== 1 ? 's' : ''}
                </span>
                <span className="text-sm text-gray-500 w-16 text-right">
                  avg {lang.avgScore?.toFixed(1)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
