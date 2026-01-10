import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import './Home.css';

function Home() {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTopicStats, setSelectedTopicStats] = useState(null);
  const [loadingStats, setLoadingStats] = useState(false);

  const navigate = useNavigate();

  useEffect(() => {
    loadTopics();
  }, []);

  const loadTopics = async () => {
    try {
      setLoading(true);
      const data = await api.getTopics();
      setTopics(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleViewProgress = async (topicId) => {
    try {
      setLoadingStats(true);
      const stats = await api.getTopicStats(topicId);
      const topic = topics.find(t => t.id === topicId);
      setSelectedTopicStats({ topic, stats });
    } catch (err) {
      alert(`Error loading progress: ${err.message}`);
    } finally {
      setLoadingStats(false);
    }
  };

  if (loading) return <div className="loading">Loading topics...</div>;

  return (
    <div className="home">
      <div className="home-header">
        <h2>Topics</h2>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="topics-list">
        {topics.map((topic) => (
          <div key={topic.id} className="topic-item">
            <div className="topic-info">
              <h3>{topic.name}</h3>
              <p className="topic-date">{new Date(topic.created_at).toLocaleDateString()}</p>
            </div>
            <div className="topic-actions">
              <button className="btn btn-primary" onClick={() => navigate(`/quiz/${topic.id}`)}>
                Quiz
              </button>
              <button className="btn btn-secondary" onClick={() => handleViewProgress(topic.id)}>
                Progress
              </button>
            </div>
          </div>
        ))}
      </div>

      {selectedTopicStats && (
        <div className="modal-overlay" onClick={() => setSelectedTopicStats(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{selectedTopicStats.topic.name} Progress</h2>
              <button className="close-btn" onClick={() => setSelectedTopicStats(null)}>&times;</button>
            </div>
            <div className="stats-list">
              {selectedTopicStats.stats.length === 0 ? (
                <p className="no-data">No progress recorded yet for this topic.</p>
              ) : (
                selectedTopicStats.stats.map((stat, idx) => (
                  <div key={idx} className="stat-item">
                    <div className="stat-info">
                      <span className="stat-name">{stat.subtopic || 'General'}</span>
                      <div className="stat-bars">
                        <div className="bar-total">
                          <div 
                            className="bar-correct" 
                            style={{ width: `${(stat.correct_answers / stat.total_answers) * 100}%` }}
                          ></div>
                        </div>
                        <span className="stat-count">{stat.correct_answers}/{stat.total_answers}</span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Home;
