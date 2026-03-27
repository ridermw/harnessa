import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import ScoreCard from '../components/ScoreCard';
import BugList from '../components/BugList';

export default function ReviewDetail() {
  const { id } = useParams();
  const [review, setReview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let interval;

    function fetchReview() {
      fetch(`/api/reviews/${id}`)
        .then((r) => {
          if (!r.ok) throw new Error('Review not found');
          return r.json();
        })
        .then((data) => {
          setReview(data);
          setLoading(false);
          if (data.status === 'completed' || data.status === 'failed') {
            clearInterval(interval);
          }
        })
        .catch((err) => {
          setError(err.message);
          setLoading(false);
        });
    }

    fetchReview();
    interval = setInterval(fetchReview, 2000);

    return () => clearInterval(interval);
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin-slow text-4xl text-harnessa-400">⟳</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-20">
        <p className="text-red-400 text-lg">{error}</p>
        <Link to="/" className="text-harnessa-400 mt-4 inline-block">← Back to Dashboard</Link>
      </div>
    );
  }

  const verdictColors = {
    PASS: 'bg-green-500/20 border-green-500/50 text-green-400',
    NEEDS_IMPROVEMENT: 'bg-yellow-500/20 border-yellow-500/50 text-yellow-400',
    FAIL: 'bg-red-500/20 border-red-500/50 text-red-400',
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <Link to="/" className="text-harnessa-400 hover:text-harnessa-300 text-sm">← Back to Dashboard</Link>
          <h1 className="text-2xl font-bold text-white mt-2">
            Review #{id.substring(0, 8)}
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            {review.language} · {new Date(review.created_at).toLocaleString()}
          </p>
        </div>
        {review.verdict && (
          <div className={`px-6 py-3 rounded-xl border-2 text-2xl font-bold ${verdictColors[review.verdict]}`}>
            {review.verdict === 'PASS' ? '✅ ' : review.verdict === 'FAIL' ? '❌ ' : '⚠️ '}
            {review.verdict.replace('_', ' ')}
          </div>
        )}
      </div>

      {review.status === 'analyzing' && (
        <div className="bg-harnessa-500/10 border border-harnessa-500/30 rounded-xl p-6 text-center">
          <div className="animate-spin-slow text-3xl text-harnessa-400 inline-block">⟳</div>
          <p className="text-harnessa-300 mt-3 font-medium">Analysis in progress...</p>
          <p className="text-gray-400 text-sm mt-1">The trio is reviewing your code. This usually takes 5-8 seconds.</p>
        </div>
      )}

      {review.scores && (
        <>
          {/* Overall Score */}
          <div className="text-center">
            <div className="text-6xl font-bold text-white">
              <span className={
                review.overall_score >= 7 ? 'text-green-400' :
                review.overall_score >= 5 ? 'text-yellow-400' :
                'text-red-400'
              }>
                {review.overall_score?.toFixed(1)}
              </span>
              <span className="text-2xl text-gray-500">/10</span>
            </div>
            <p className="text-gray-400 mt-2">
              {review.evaluator_output?.summary || 'Overall quality score'}
            </p>
          </div>

          {/* Score Cards */}
          <div>
            <h2 className="text-lg font-semibold text-white mb-4">Quality Scores</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              {Object.entries(review.scores).map(([key, value]) => (
                <ScoreCard
                  key={key}
                  label={key.replace(/([A-Z])/g, ' $1').replace(/^./, (s) => s.toUpperCase())}
                  value={value}
                />
              ))}
            </div>
          </div>
        </>
      )}

      {/* Bugs */}
      {review.bugs && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">
            Issues Found ({review.bugs.length})
          </h2>
          <BugList bugs={review.bugs} />
        </div>
      )}

      {/* Code */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Submitted Code</h2>
        <pre className="bg-gray-900 border border-gray-800 rounded-lg p-4 overflow-x-auto text-sm text-gray-300 font-mono leading-6">
          {review.code}
        </pre>
      </div>

      {/* Trio Phase Details */}
      {review.planner_output && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-harnessa-400 mb-2">📋 Planner Output</h3>
            <p className="text-sm text-gray-300">{review.planner_output.summary}</p>
            <p className="text-xs text-gray-500 mt-2">
              Complexity: {review.planner_output.complexity} · {review.planner_output.lineCount} lines · {review.planner_output.functionCount} function(s)
            </p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-harnessa-400 mb-2">🔍 Generator Output</h3>
            <p className="text-sm text-gray-300">{review.generator_output?.analysisNotes}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-harnessa-400 mb-2">⚖️ Evaluator Output</h3>
            <p className="text-sm text-gray-300">{review.evaluator_output?.summary}</p>
          </div>
        </div>
      )}
    </div>
  );
}
