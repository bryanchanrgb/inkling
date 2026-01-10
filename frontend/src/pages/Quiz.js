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
    loadQuiz();
  }, [topicId]);

  const loadQuiz = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.startQuiz(parseInt(topicId));
      if (data.length === 0) {
        setError('No questions available for this topic. Please generate some questions first.');
        return;
      }
      setQuestions(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!userAnswer.trim()) {
      alert('Please enter an answer');
      return;
    }

    const currentQuestion = questions[currentQuestionIndex];
    try {
      setGrading(true);
      const gradedAnswer = await api.gradeAnswer(currentQuestion.id, userAnswer.trim());
      
      setCurrentFeedback(gradedAnswer);
      setAnswers([...answers, gradedAnswer]);
      setShowFeedback(true);
    } catch (err) {
      alert(`Error grading answer: ${err.message}`);
    } finally {
      setGrading(false);
    }
  };

  const handleNextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      setUserAnswer('');
      setShowFeedback(false);
      setCurrentFeedback(null);
    } else {
      // Quiz complete - calculate results
      finishQuiz();
    }
  };

  const finishQuiz = async () => {
    try {
      const quizResults = await api.getQuizResults(answers);
      setResults(quizResults);
    } catch (err) {
      alert(`Error calculating results: ${err.message}`);
    }
  };

  const handleFinish = () => {
    navigate('/');
  };

  if (loading) {
    return <div className="loading">Loading quiz...</div>;
  }

  if (error) {
    return (
      <div className="quiz-error">
        <div className="error">{error}</div>
        <button className="btn btn-primary" onClick={() => navigate('/')}>
          Go Back
        </button>
      </div>
    );
  }

  if (results) {
    return (
      <div className="quiz-results">
        <div className="card">
          <h2>Quiz Results</h2>
          <div className="results-stats">
            <div className="stat">
              <div className="stat-label">Total Questions</div>
              <div className="stat-value">{results.total_questions}</div>
            </div>
            <div className="stat">
              <div className="stat-label">Correct</div>
              <div className="stat-value correct">{results.correct_answers}</div>
            </div>
            <div className="stat">
              <div className="stat-label">Incorrect</div>
              <div className="stat-value incorrect">{results.incorrect_answers}</div>
            </div>
            <div className="stat">
              <div className="stat-label">Score</div>
              <div className="stat-value score">{results.score.toFixed(1)}%</div>
            </div>
            <div className="stat">
              <div className="stat-label">Avg Understanding</div>
              <div className="stat-value">{results.average_understanding.toFixed(1)}/5</div>
            </div>
          </div>
          <div className={`performance-message ${results.score >= 80 ? 'excellent' : results.score >= 60 ? 'good' : 'needs-improvement'}`}>
            {results.score >= 80
              ? 'Excellent work!'
              : results.score >= 60
              ? 'Good job! Keep practicing.'
              : "Keep studying! You'll improve with practice."}
          </div>
          <button className="btn btn-primary" onClick={handleFinish}>
            Finish
          </button>
        </div>
      </div>
    );
  }

  if (questions.length === 0) {
    return <div className="loading">No questions available</div>;
  }

  const currentQuestion = questions[currentQuestionIndex];
  const progress = ((currentQuestionIndex + (showFeedback ? 1 : 0)) / questions.length) * 100;

  return (
    <div className="quiz">
      <div className="quiz-header">
        <h2>Quiz</h2>
        <div className="quiz-progress">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }}></div>
          </div>
          <div className="progress-text">
            Question {currentQuestionIndex + 1} of {questions.length}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="question-header">
          {currentQuestion.subtopic && (
            <span className="badge badge-info">Subtopic: {currentQuestion.subtopic}</span>
          )}
          {currentQuestion.difficulty && (
            <span className={`badge badge-difficulty ${currentQuestion.difficulty}`}>
              {currentQuestion.difficulty}
            </span>
          )}
        </div>
        <h3 className="question-text">{currentQuestion.question_text}</h3>

        {!showFeedback ? (
          <div className="answer-section">
            <textarea
              className="input answer-input"
              placeholder="Type your answer here..."
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
              rows="6"
              disabled={grading}
            />
            <button
              className="btn btn-primary"
              onClick={handleSubmitAnswer}
              disabled={grading || !userAnswer.trim()}
            >
              {grading ? 'Grading...' : 'Submit Answer'}
            </button>
          </div>
        ) : (
          <div className="feedback-section">
            <div className={`feedback ${currentFeedback.is_correct ? 'correct' : 'incorrect'}`}>
              <div className="feedback-icon">
                {currentFeedback.is_correct ? '✓' : '✗'}
              </div>
              <div className="feedback-content">
                <h4>{currentFeedback.is_correct ? 'Correct!' : 'Incorrect'}</h4>
                {currentFeedback.feedback && (
                  <p className="feedback-text">{currentFeedback.feedback}</p>
                )}
                {currentFeedback.understanding_score && (
                  <p className="understanding-score">
                    Understanding Score: {currentFeedback.understanding_score}/5
                  </p>
                )}
              </div>
            </div>
            <button className="btn btn-primary" onClick={handleNextQuestion}>
              {currentQuestionIndex < questions.length - 1 ? 'Next Question' : 'Finish Quiz'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default Quiz;

