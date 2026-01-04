"""Quiz service for managing quizzes and grading answers."""

import random
from datetime import datetime
from typing import List, Optional

from .ai_service import get_ai_service
from .config import get_config
from .models import Answer, Question, Topic
from .storage import Storage


class QuizService:
    """Service for managing quizzes."""
    
    def __init__(self):
        """Initialize quiz service."""
        self.ai_service = get_ai_service()
        self.storage = Storage()
        self.config = get_config()
    
    def start_quiz(self, topic_id: int, num_questions: Optional[int] = None) -> List[Question]:
        """Start a quiz for a topic.
        
        Args:
            topic_id: ID of the topic to quiz on
            num_questions: Number of questions to include (default from config)
            
        Returns:
            List of questions for the quiz
        """
        if num_questions is None:
            num_questions = self.config.get_app_config().get('quiz_questions_per_session', 5)
        
        # Get all questions for the topic
        all_questions = self.storage.get_questions_for_topic(topic_id)
        
        if not all_questions:
            raise ValueError(f"No questions found for topic ID {topic_id}")
        
        # Randomly select questions
        if len(all_questions) <= num_questions:
            return all_questions
        else:
            return random.sample(all_questions, num_questions)
    
    def grade_answer(self, question: Question, user_answer: str) -> Answer:
        """Grade a user's answer using LLM.
        
        Args:
            question: The question being answered
            user_answer: The user's answer
            
        Returns:
            Answer object with grading results
        """
        # Use AI service to grade the answer
        is_correct, confidence_score, feedback = self.ai_service.grade_answer(
            question.question_text,
            question.correct_answer,
            user_answer
        )
        
        # Create answer object
        answer = Answer(
            question_id=question.id,
            user_answer=user_answer,
            is_correct=is_correct,
            confidence_score=confidence_score,
            feedback=feedback,
            timestamp=datetime.now()
        )
        
        # Save answer to database
        answer_id = self.storage.save_answer(answer)
        answer.id = answer_id
        
        return answer
    
    def get_quiz_results(self, answers: List[Answer]) -> dict:
        """Calculate quiz results from a list of answers.
        
        Args:
            answers: List of answers from the quiz
            
        Returns:
            Dictionary with quiz statistics
        """
        total = len(answers)
        correct = sum(1 for a in answers if a.is_correct)
        score = (correct / total * 100) if total > 0 else 0.0
        avg_confidence = sum(a.confidence_score or 0.0 for a in answers) / total if total > 0 else 0.0
        
        return {
            'total_questions': total,
            'correct_answers': correct,
            'incorrect_answers': total - correct,
            'score': score,
            'average_confidence': avg_confidence
        }
    
    def get_quiz_history(self, topic_id: Optional[int] = None, limit: int = 10) -> List[dict]:
        """Get quiz history for a topic or all topics.
        
        Args:
            topic_id: Optional topic ID to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of quiz history records
        """
        return self.storage.get_quiz_history(topic_id, limit)

