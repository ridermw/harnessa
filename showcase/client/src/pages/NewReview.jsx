import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import CodeEditor from '../components/CodeEditor';
import TrioProgress from '../components/TrioProgress';
import useSocket from '../hooks/useSocket';

const LANGUAGES = ['javascript', 'typescript', 'python', 'java', 'go', 'rust', 'c', 'cpp', 'ruby', 'php'];

const SAMPLE_CODE = `// Try submitting this code — the trio will find real issues!
function processUserData(data) {
  const apiKey = "sk-secret-key-12345";
  
  console.log("Processing:", data);
  
  // TODO: add validation
  // FIXME: this function is way too long
  
  if (data) {
    if (data.users) {
      if (data.users.length > 0) {
        for (let i = 0; i < data.users.length; i++) {
          if (data.users[i].active) {
            if (data.users[i].email) {
              // process user
              console.log(data.users[i]);
            }
          }
        }
      }
    }
  }
}

async function fetchData() {
  const response = await fetch("/api/data");
  const json = await response.json();
  return json;
}`;

export default function NewReview() {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('javascript');
  const [submitting, setSubmitting] = useState(false);
  const [reviewId, setReviewId] = useState(null);
  const [phaseStates, setPhaseStates] = useState({});
  const [complete, setComplete] = useState(false);
  const navigate = useNavigate();
  const socket = useSocket();

  useEffect(() => {
    if (!socket || !reviewId) return;

    function onPhase(data) {
      if (data.reviewId === reviewId) {
        setPhaseStates((prev) => ({ ...prev, [data.phase]: data.status }));
      }
    }

    function onComplete(data) {
      if (data.reviewId === reviewId) {
        setComplete(true);
      }
    }

    socket.on('trio_phase', onPhase);
    socket.on('review_complete', onComplete);

    return () => {
      socket.off('trio_phase', onPhase);
      socket.off('review_complete', onComplete);
    };
  }, [socket, reviewId]);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!code.trim()) return;

    setSubmitting(true);
    setPhaseStates({});
    setComplete(false);

    try {
      const res = await fetch('/api/reviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language }),
      });
      const data = await res.json();
      setReviewId(data.id);
    } catch (err) {
      console.error('Submit failed:', err);
      setSubmitting(false);
    }
  }

  function loadSample() {
    setCode(SAMPLE_CODE);
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white">New Code Review</h1>
        <p className="text-gray-400 mt-1">
          Submit code for AI-powered trio analysis (Planner → Generator → Evaluator)
        </p>
      </div>

      {!reviewId ? (
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium text-gray-300">Language:</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="bg-gray-800 border border-gray-700 text-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-harnessa-500 focus:border-harnessa-500"
              >
                {LANGUAGES.map((lang) => (
                  <option key={lang} value={lang}>{lang}</option>
                ))}
              </select>
            </div>
            <button
              type="button"
              onClick={loadSample}
              className="text-sm text-harnessa-400 hover:text-harnessa-300 transition-colors"
            >
              Load sample code with bugs →
            </button>
          </div>

          <CodeEditor value={code} onChange={setCode} language={language} />

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={!code.trim() || submitting}
              className="bg-harnessa-500 hover:bg-harnessa-600 disabled:opacity-50 disabled:cursor-not-allowed text-white px-8 py-3 rounded-lg font-semibold transition-colors text-lg"
            >
              🔍 Analyze Code
            </button>
          </div>
        </form>
      ) : (
        <div className="space-y-6">
          <TrioProgress phaseStates={phaseStates} />

          {complete && (
            <div className="animate-fade-in text-center space-y-4 pt-4">
              <div className="text-2xl">✅ Analysis Complete!</div>
              <button
                onClick={() => navigate(`/review/${reviewId}`)}
                className="bg-harnessa-500 hover:bg-harnessa-600 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
              >
                View Results →
              </button>
              <button
                onClick={() => {
                  setReviewId(null);
                  setSubmitting(false);
                  setCode('');
                  setPhaseStates({});
                  setComplete(false);
                }}
                className="block mx-auto text-gray-400 hover:text-gray-300 text-sm transition-colors mt-2"
              >
                Submit another review
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
