import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import './Home.css';

function Home() {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [generating, setGenerating] = useState({});

  const navigate = useNavigate();

  useEffect(() => {
    loadTopics();
  }, []);

  const loadTopics = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getTopics();
      setTopics(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleStartQuiz = (topicId) => {
    navigate(`/quiz/${topicId}`);
  };

  const handleGenerateQuestions = async (topicId) => {
    try {
      setGenerating({ ...generating, [topicId]: true });
      await api.generateAdditionalQuestions(topicId);
      alert('Additional questions generated successfully!');
      loadTopics(); // Refresh to show updated question count
    } catch (err) {
      alert(`Error generating questions: ${err.message}`);
    } finally {
      setGenerating({ ...generating, [topicId]: false });
    }
  };

  if (loading) {
    return <div className="loading">Loading topics...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  return (
    <div className="home">
      <div className="home-header">
        <h2>Topics</h2>
        <Link to="/create-topic" className="btn btn-primary">
          Create New Topic
        </Link>
      </div>

      {topics.length === 0 ? (
        <div className="card">
          <p>No topics yet. Create your first topic to get started!</p>
        </div>
      ) : (
        <div className="topics-grid">
          {topics.map((topic) => (
            <div key={topic.id} className="topic-card">
              <h3>{topic.name}</h3>
              {topic.description && <p className="topic-description">{topic.description}</p>}
              {topic.created_at && (
                <p className="topic-date">Created: {new Date(topic.created_at).toLocaleDateString()}</p>
              )}
              <div className="topic-actions">
                <button
                  className="btn btn-primary"
                  onClick={() => handleStartQuiz(topic.id)}
                >
                  Start Quiz
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() => handleGenerateQuestions(topic.id)}
                  disabled={generating[topic.id]}
                >
                  {generating[topic.id] ? 'Generating...' : 'Generate Questions'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Home;

