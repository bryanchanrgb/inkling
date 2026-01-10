import React, { useState, useEffect } from 'react';
import api from '../services/api';
import './QuizHistory.css';

function QuizHistory() {
  const [history, setHistory] = useState([]);
  const [topics, setTopics] = useState([]);
  const [selectedTopicId, setSelectedTopicId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadTopics();
  }, []);

  useEffect(() => {
    loadHistory();
  }, [selectedTopicId]);

  const loadTopics = async () => {
    try {
      const data = await api.getTopics();
      setTopics(data);
    } catch (err) {
      console.error('Error loading topics:', err);
    }
  };

  const loadHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getQuizHistory(selectedTopicId, 50);
      setHistory(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading && history.length === 0) {
    return <div className="loading">Loading history...</div>;
  }

  return (
    <div className="quiz-history">
      <div className="history-header">
        <h2>Quiz History</h2>
        <div className="topic-filter">
          <label htmlFor="topic-select">Filter by topic:</label>
          <select
            id="topic-select"
            className="input"
            value={selectedTopicId || ''}
            onChange={(e) => setSelectedTopicId(e.target.value ? parseInt(e.target.value) : null)}
          >
            <option value="">All Topics</option>
            {topics.map((topic) => (
              <option key={topic.id} value={topic.id}>
                {topic.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {history.length === 0 ? (
        <div className="card">
          <p>No quiz history found.</p>
        </div>
      ) : (
        <div className="history-table-container">
          <table className="history-table">
            <thead>
              <tr>
                <th>Question</th>
                <th>Your Answer</th>
                <th>Correct</th>
                <th>Score</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {history.map((entry) => (
                <tr key={entry.id}>
                  <td className="question-cell">
                    <div className="question-text">{entry.question_text}</div>
                    {entry.topic_name && (
                      <div className="topic-name">{entry.topic_name}</div>
                    )}
                  </td>
                  <td className="answer-cell">{entry.user_answer}</td>
                  <td className="correct-cell">
                    <span className={`correct-badge ${entry.is_correct ? 'correct' : 'incorrect'}`}>
                      {entry.is_correct ? '✓' : '✗'}
                    </span>
                  </td>
                  <td className="score-cell">
                    {entry.understanding_score ? `${entry.understanding_score}/5` : 'N/A'}
                  </td>
                  <td className="date-cell">
                    {new Date(entry.timestamp).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default QuizHistory;

