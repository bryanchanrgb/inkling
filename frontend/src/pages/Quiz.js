import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import './Quiz.css';

function Quiz() {
  const { topicId } = useParams();
  const navigate = useNavigate();
  
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswer, setUserAnswer] = useState('');
  const [answers, setAnswers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [grading, setGrading] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [currentFeedback, setCurrentFeedback] = useState(null);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);

  useEffect(() => {
    const loadQuiz = async () => {
      try {
        setLoading(true);
        const data = await api.startQuiz(parseInt(topicId));
        if (data.length === 0) {
          setError('No questions available. Try generating more.');
          return;
        }
        setQuestions(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadQuiz();
  }, [topicId]);

  const handleSubmitAnswer = async () => {
    if (!userAnswer.trim()) return;

    try {
      setGrading(true);
      const graded = await api.gradeAnswer(questions[currentQuestionIndex].id, userAnswer.trim());
      setCurrentFeedback(graded);
      setAnswers([...answers, graded]);
      setShowFeedback(true);
    } catch (err) {
      alert(err.message);
    } finally {
      setGrading(false);
    }
  };

  const finishQuiz = async () => {
    try {
      const res = await api.getQuizResults(answers);
      setResults(res);
    } catch (err) {
      alert(err.message);
    }
  };

  if (loading) return <div className="loading">Preparing Session...</div>;

  if (results) {
    return (
      <div className="quiz-complete">
        <div className="results-header">
          <h2>Results</h2>
          <div className="score-big">{results.score.toFixed(0)}%</div>
        </div>
        
        <div className="stats-grid">
          <div className="stat-box">
            <span className="label">Accuracy</span>
            <span className="value">{results.correct_answers}/{results.total_questions}</span>
          </div>
          <div className="stat-box">
            <span className="label">Understanding</span>
            <span className="value">{results.average_understanding.toFixed(1)}/5</span>
          </div>
        </div>

        <button className="btn btn-primary" onClick={() => navigate('/')}>Continue</button>
      </div>
    );
  }

  const q = questions[currentQuestionIndex];

  return (
    <div className="quiz-session">
      <div className="quiz-meta">
        <span className="q-count">Question {currentQuestionIndex + 1} / {questions.length}</span>
        {q?.subtopic && <span className="q-subtopic">{q.subtopic}</span>}
      </div>

      <div className="question-display">
        <h3>{q?.question_text}</h3>
        
        {!showFeedback ? (
          <div className="answer-area">
            <textarea
              className="input answer-input"
              placeholder="Your response..."
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
              rows="4"
              disabled={grading}
            />
            <button 
              className="btn btn-primary" 
              onClick={handleSubmitAnswer}
              disabled={grading || !userAnswer.trim()}
            >
              {grading ? 'Grading...' : 'Submit'}
            </button>
          </div>
        ) : (
          <div className="feedback-area">
            <div className={`feedback-tag ${currentFeedback.is_correct ? 'correct' : 'incorrect'}`}>
              {currentFeedback.is_correct ? 'CORRECT' : 'INCORRECT'}
            </div>
            <p className="feedback-text">{currentFeedback.feedback}</p>
            <button className="btn btn-primary" onClick={() => {
              if (currentQuestionIndex < questions.length - 1) {
                setCurrentQuestionIndex(prev => prev + 1);
                setUserAnswer('');
                setShowFeedback(false);
              } else {
                finishQuiz();
              }
            }}>
              {currentQuestionIndex < questions.length - 1 ? 'Next' : 'Finish'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default Quiz;
