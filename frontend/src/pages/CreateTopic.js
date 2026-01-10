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
    if (!topicName.trim()) return;

    try {
      setLoading(true);
      setError(null);
      await api.createTopic(topicName.trim());
      navigate('/');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="create-topic">
      <h2>Add Topic</h2>
      <p className="description">
        Enter a subject to begin. We'll generate a curated set of subtopics and questions to guide your learning.
      </p>
      
      <form onSubmit={handleSubmit} className="create-form">
        {error && <div className="error">{error}</div>}
        <input
          type="text"
          className="input"
          placeholder="e.g. Quantum Physics, Culinary Arts, French Grammar"
          value={topicName}
          onChange={(e) => setTopicName(e.target.value)}
          disabled={loading}
          autoFocus
        />
        <div className="actions">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || !topicName.trim()}
          >
            {loading ? 'Initializing...' : 'Confirm'}
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
  );
}

export default CreateTopic;
