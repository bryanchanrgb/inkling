import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import './CreateTopic.css';

function CreateTopic() {
  const [topicName, setTopicName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!topicName.trim()) {
      setError('Topic name cannot be empty');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const result = await api.createTopic(topicName.trim());
      
      alert(`Topic "${result.topic.name}" created successfully!\n\n${result.questions.length} questions generated.\n${result.subtopics.length} subtopics created.`);
      navigate('/');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="create-topic">
      <h2>Create New Topic</h2>
      <div className="card">
        <p className="info-text">
          Enter a topic name and we'll generate a knowledge graph with subtopics and quiz questions using AI.
          This may take a minute or two.
        </p>
        <form onSubmit={handleSubmit}>
          {error && <div className="error">{error}</div>}
          <input
            type="text"
            className="input"
            placeholder="Enter topic name (e.g., 'Machine Learning', 'World History')"
            value={topicName}
            onChange={(e) => setTopicName(e.target.value)}
            disabled={loading}
            autoFocus
          />
          <div className="form-actions">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !topicName.trim()}
            >
              {loading ? 'Creating Topic...' : 'Create Topic'}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => navigate('/')}
              disabled={loading}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CreateTopic;

