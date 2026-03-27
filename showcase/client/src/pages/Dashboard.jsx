import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import ActivityFeed from '../components/ActivityFeed';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch('/api/analytics').then((r) => r.json()),
      fetch('/api/reviews?limit=5').then((r) => r.json()),
    ])
      .then(([analytics, reviewsData]) => {
        setStats(analytics);
        setReviews(reviewsData.reviews || []);
      })
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

  const metricCards = [
    { label: 'Total Reviews', value: stats?.totalReviews ?? 0, color: 'purple' },
    { label: 'Average Score', value: stats?.averageScore ?? 0, color: (stats?.averageScore ?? 0) >= 7 ? 'green' : (stats?.averageScore ?? 0) >= 5 ? 'yellow' : 'red' },
    { label: 'Pass Rate', value: `${stats?.passRate ?? 0}%`, color: (stats?.passRate ?? 0) >= 70 ? 'green' : (stats?.passRate ?? 0) >= 50 ? 'yellow' : 'red' },
    { label: 'Reviews Today', value: stats?.reviewsToday ?? 0, color: 'purple' },
  ];

  const colorClasses = {
    green: 'bg-green-500/10 border-green-500/30 text-green-400',
    yellow: 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400',
    red: 'bg-red-500/10 border-red-500/30 text-red-400',
    purple: 'bg-harnessa-500/10 border-harnessa-500/30 text-harnessa-300',
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400 mt-1">Overview of your code review activity</p>
        </div>
        <Link
          to="/new"
          className="bg-harnessa-500 hover:bg-harnessa-600 text-white px-5 py-2.5 rounded-lg font-medium transition-colors"
        >
          + New Review
        </Link>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {metricCards.map((card) => (
          <div key={card.label} className={`rounded-xl border p-5 ${colorClasses[card.color]}`}>
            <div className="text-sm font-medium opacity-70">{card.label}</div>
            <div className="text-3xl font-bold mt-2">
              {typeof card.value === 'number' && card.label === 'Average Score'
                ? card.value.toFixed(1)
                : card.value}
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Reviews */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-lg font-semibold text-white">Recent Reviews</h2>
          {reviews.length === 0 ? (
            <div className="bg-gray-900 rounded-lg border border-gray-800 p-8 text-center">
              <p className="text-gray-500">No reviews yet.</p>
              <Link to="/new" className="text-harnessa-400 hover:text-harnessa-300 text-sm mt-2 inline-block">
                Submit your first review →
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {reviews.map((review) => (
                <Link
                  key={review.id}
                  to={`/review/${review.id}`}
                  className="block bg-gray-900 rounded-lg border border-gray-800 p-4 hover:border-harnessa-500/50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        review.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                        review.status === 'analyzing' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-gray-500/20 text-gray-400'
                      }`}>
                        {review.status}
                      </span>
                      <span className="text-sm text-gray-400">{review.language}</span>
                    </div>
                    <div className="flex items-center gap-4">
                      {review.overall_score != null && (
                        <span className={`text-lg font-bold ${
                          review.overall_score >= 7 ? 'text-green-400' :
                          review.overall_score >= 5 ? 'text-yellow-400' :
                          'text-red-400'
                        }`}>
                          {review.overall_score.toFixed(1)}
                        </span>
                      )}
                      {review.verdict && (
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                          review.verdict === 'PASS' ? 'bg-green-500/20 text-green-400' :
                          review.verdict === 'NEEDS_IMPROVEMENT' ? 'bg-yellow-500/20 text-yellow-400' :
                          'bg-red-500/20 text-red-400'
                        }`}>
                          {review.verdict}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="mt-2 text-sm text-gray-500 font-mono truncate">
                    {review.code?.substring(0, 100)}...
                  </div>
                  <div className="mt-2 text-xs text-gray-600">
                    {new Date(review.created_at).toLocaleString()} · #{review.id.substring(0, 8)}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Activity Feed */}
        <div>
          <ActivityFeed />
        </div>
      </div>
    </div>
  );
}
