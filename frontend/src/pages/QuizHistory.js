import React, { useState, useEffect } from 'react';
import api from '../services/api';
import './QuizHistory.css';

function QuizHistory() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await api.getQuizHistory(null, 50);
        setHistory(data);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <div className="loading">Loading History...</div>;

  return (
    <div className="history">
      <div className="history-header">
        <h2>History</h2>
      </div>

      <div className="history-list">
        {history.length === 0 ? (
          <p className="no-data">No recorded attempts.</p>
        ) : (
          history.map((entry) => (
            <div key={entry.id} className="history-item">
              <div className="history-main">
                <span className={`status-dot ${entry.is_correct ? 'correct' : 'incorrect'}`}></span>
                <div className="history-details">
                  <p className="history-q">{entry.question_text}</p>
                  <p className="history-meta">
                    {entry.topic_name} — {new Date(entry.timestamp).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <div className="history-score">
                {entry.understanding_score}/5
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default QuizHistory;
