import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/Header';
import Home from './pages/Home';
import CreateTopic from './pages/CreateTopic';
import Quiz from './pages/Quiz';
import QuizHistory from './pages/QuizHistory';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Header />
        <div className="container">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/create-topic" element={<CreateTopic />} />
            <Route path="/quiz/:topicId" element={<Quiz />} />
            <Route path="/history" element={<QuizHistory />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;

