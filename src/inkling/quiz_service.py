"""Quiz service for managing quizzes and grading answers."""

import json
import random
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .ai_service import get_ai_service
from .config import get_config
from .models import Answer, Question, Topic
from .storage import Storage


# Question generation prompts
QUESTION_GENERATION_SYSTEM_MESSAGE = "You are a quiz question generator. Always return valid JSON only."

QUESTION_GENERATION_PROMPT_TEMPLATE = """Generate {count} quiz questions for the topic: "{topic_name}".

Knowledge Graph:
{knowledge_graph}

For each question, provide:
- question_text: The question
- correct_answer: The correct answer
- subtopic: Which subtopic this question relates to
- difficulty: easy, medium, or hard

Return a JSON array of questions:
[
    {{
        "question_text": "Question here?",
        "correct_answer": "Correct answer",
        "subtopic": "Subtopic name",
        "difficulty": "medium"
    }}
]

Only return the JSON array, no additional text."""

# Grading prompts
GRADING_SYSTEM_MESSAGE = "You are an educational quiz grader. Always return valid JSON only."

GRADING_PROMPT_TEMPLATE = """You are grading a quiz answer. Evaluate the user's answer for correctness.

Question: {question}
Correct Answer: {correct_answer}
User's Answer: {user_answer}

Evaluate whether the user's answer is correct. Consider:
- Conceptual understanding (not just exact word matching)
- Partial correctness
- Common misconceptions

Return a JSON object with:
{{
    "is_correct": true/false,
    "confidence_score": 0.0-1.0,
    "feedback": "Brief explanation of why the answer is correct or incorrect, and what the correct answer should be"
}}

Only return the JSON object, no additional text."""


def _extract_json_content(content: str) -> str:
    """Extract JSON from response content, removing markdown code blocks if present."""
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    return content


class QuizService:
    """Service for managing quizzes."""
    
    def __init__(self):
        """Initialize quiz service."""
        self.ai_service = get_ai_service()
        self.storage = Storage()
        self.config = get_config()
    
    def generate_questions(self, topic_name: str, knowledge_graph: Dict[str, Any], count: int = 10) -> List[Dict[str, Any]]:
        """Generate questions based on a knowledge graph using AI.
        
        Args:
            topic_name: Name of the topic
            knowledge_graph: Knowledge graph structure
            count: Number of questions to generate
            
        Returns:
            List of question dictionaries
        """
        # Get generation parameters from config
        qg_config = self.config.get('ai.question_generation', {})
        temperature = qg_config.get('temperature', 0.8)
        max_tokens = qg_config.get('max_tokens', 4000)
        
        # Format knowledge graph as string
        graph_str = json.dumps(knowledge_graph, indent=2)
        
        # Generate prompt
        prompt = QUESTION_GENERATION_PROMPT_TEMPLATE.format(
            topic_name=topic_name,
            knowledge_graph=graph_str,
            count=count
        )
        
        # Call AI model
        response = self.ai_service.call_model(
            system_message=QUESTION_GENERATION_SYSTEM_MESSAGE,
            user_message=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Extract and parse JSON
        content = _extract_json_content(response)
        return json.loads(content)
    
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
        # Get grading parameters from config
        grading_config = self.config.get('ai.grading', {})
        temperature = grading_config.get('temperature', 0.3)
        max_tokens = grading_config.get('max_tokens', 1000)
        
        # Generate prompt
        prompt = GRADING_PROMPT_TEMPLATE.format(
            question=question.question_text,
            correct_answer=question.correct_answer,
            user_answer=user_answer
        )
        
        # Call AI model
        response = self.ai_service.call_model(
            system_message=GRADING_SYSTEM_MESSAGE,
            user_message=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Extract and parse JSON
        content = _extract_json_content(response)
        result = json.loads(content)
        
        is_correct = result.get('is_correct', False)
        confidence_score = result.get('confidence_score', 0.0)
        feedback = result.get('feedback', '')
        
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

