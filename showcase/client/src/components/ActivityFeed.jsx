import { useEffect, useState } from 'react';
import useSocket from '../hooks/useSocket';

export default function ActivityFeed() {
  const [activities, setActivities] = useState([]);
  const socket = useSocket();

  useEffect(() => {
    // Load recent activity from analytics
    fetch('/api/analytics')
      .then((r) => r.json())
      .then((data) => {
        if (data.recentActivity) {
          setActivities(data.recentActivity.slice(0, 15).map((a) => ({
            id: a.id,
            type: a.type,
            description: a.description,
            timestamp: a.created_at,
          })));
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!socket) return;

    const handler = (data) => {
      setActivities((prev) => [
        { id: Date.now().toString(), ...data },
        ...prev.slice(0, 19),
      ]);
    };

    socket.on('activity', handler);
    return () => socket.off('activity', handler);
  }, [socket]);

  const typeIcons = {
    review_started: '🚀',
    phase_completed: '⚡',
    review_completed: '✅',
    review_failed: '❌',
  };

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
        Live Activity
      </h3>
      {activities.length === 0 ? (
        <p className="text-gray-500 text-sm py-4 text-center">No activity yet. Submit a review to get started!</p>
      ) : (
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {activities.map((activity) => (
            <div
              key={activity.id}
              className="flex items-start gap-2 text-sm animate-fade-in py-1.5 border-b border-gray-800/50 last:border-0"
            >
              <span className="flex-shrink-0 mt-0.5">{typeIcons[activity.type] || '📋'}</span>
              <span className="text-gray-300 flex-1">{activity.description}</span>
              <span className="text-gray-600 text-xs whitespace-nowrap flex-shrink-0">
                {activity.timestamp ? new Date(activity.timestamp).toLocaleTimeString() : ''}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
