"""Quiz service for managing quizzes and grading answers."""

import json
import random
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .ai_service import get_ai_service
from .config import get_config
from .knowledge_graph import KnowledgeGraph
from .models import Answer, Question, Topic
from .storage import Storage


# Question generation prompts
QUESTION_GENERATION_SYSTEM_MESSAGE = "You are a quiz question generator. Always return valid JSON only."

# Shared question output format instructions
QUESTION_OUTPUT_FORMAT = """For each question, provide:
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

QUESTION_GENERATION_PROMPT_TEMPLATE = """Generate {count} quiz questions for the topic: "{topic_name}".

Knowledge Graph:
{knowledge_graph}

{question_output_format}"""

ADDITIONAL_QUESTIONS_PROMPT_TEMPLATE = """Generate {count} NEW quiz questions for the topic: "{topic_name}".

Knowledge Graph:
{knowledge_graph}

EXISTING QUESTIONS (DO NOT DUPLICATE THESE):
{existing_questions}

LEARNING GAPS TO ADDRESS:
{learning_gaps}

Generate questions that:
1. Do NOT duplicate any existing questions above
2. Focus on subtopics where the user needs improvement (see learning gaps)
3. If no specific gaps, enrich the knowledge graph with new perspectives
4. Cover subtopics that don't have questions yet
5. Match the style and format of existing questions

{question_output_format}"""

# Grading prompts
GRADING_SYSTEM_MESSAGE = "You are an educational quiz grader. Always return valid JSON only."

GRADING_PROMPT_TEMPLATE = """You are grading a quiz answer. Evaluate the user's answer for correctness and understanding.

Question: {question}
Correct Answer: {correct_answer}
User's Answer: {user_answer}

Evaluate the user's answer and assign an understanding_score from 1 to 5:
- 1: Answer is nonexistent or completely incorrect, showing no understanding
- 2: Answer is not correct but demonstrates some understanding of the concept
- 3: Partially correct answer demonstrating reasonable understanding
- 4: Correct answer but with some details or nuances missed
- 5: Perfect answer demonstrating complete understanding

Consider:
- Conceptual understanding (not just exact word matching)
- Partial correctness
- Common misconceptions
- Depth of understanding demonstrated

Return a JSON object with:
{{
    "is_correct": true/false,
    "understanding_score": 1-5,
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
        self.knowledge_graph = KnowledgeGraph()
    
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
            count=count,
            question_output_format=QUESTION_OUTPUT_FORMAT
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
    
    def generate_additional_questions(
        self, 
        topic_id: int, 
        count: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Generate additional questions based on knowledge graph state and learning gaps.
        
        This method analyzes existing questions, answer history, and understanding scores
        to generate new questions that:
        - Don't duplicate existing questions
        - Target areas where the user needs improvement
        - Enrich the knowledge graph with new information
        
        Args:
            topic_id: ID of the topic to generate questions for
            count: Number of new questions to generate (defaults to config value)
            
        Returns:
            List of new question dictionaries
        """
        # Get count from config if not provided
        if count is None:
            count = self.config.get_app_config().get('additional_questions_count', 5)
        # Get topic information
        topic = self.storage.get_topic(topic_id)
        if not topic:
            raise ValueError(f"Topic with ID {topic_id} not found")
        
        topic_name = topic.name
        
        # Get existing questions
        existing_questions = self.storage.get_questions_for_topic(topic_id)
        
        # Get answer statistics to identify learning gaps
        answer_stats = self.storage.get_question_answer_stats(topic_id)
        
        # Get knowledge graph structure
        subtopics = self.knowledge_graph.get_subtopics(topic_name)
        knowledge_graph = {
            "subtopics": [
                {
                    "name": st["name"],
                    "description": st.get("description", "")
                }
                for st in subtopics
            ]
        }
        
        # Get understanding scores for all questions in a single query
        question_ids = [q.id for q in existing_questions]
        understanding_scores = {}
        
        if question_ids:
            conn = sqlite3.connect(str(self.storage.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(question_ids))
            cursor.execute(f"""
                WITH LatestAnswers AS (
                    SELECT 
                        question_id,
                        understanding_score,
                        ROW_NUMBER() OVER (PARTITION BY question_id ORDER BY timestamp DESC) as rn
                    FROM answers
                    WHERE question_id IN ({placeholders})
                )
                SELECT question_id, understanding_score
                FROM LatestAnswers
                WHERE rn = 1
            """, question_ids)
            
            for row in cursor.fetchall():
                understanding_scores[row['question_id']] = row['understanding_score']
            conn.close()
        
        # Identify learning gaps: subtopics with low understanding or incorrect answers
        learning_gaps = []
        subtopic_performance = {}
        
        for question in existing_questions:
            stats = answer_stats.get(question.id, {})
            subtopic = question.subtopic
            
            if subtopic:
                if subtopic not in subtopic_performance:
                    subtopic_performance[subtopic] = {
                        'total_questions': 0,
                        'low_understanding': 0,  # understanding_score <= 2
                        'incorrect_answers': 0,
                        'avg_understanding': []
                    }
                
                subtopic_performance[subtopic]['total_questions'] += 1
                
                if stats.get('has_answers'):
                    if stats.get('last_answer_correct') is False:
                        subtopic_performance[subtopic]['incorrect_answers'] += 1
                    
                    # Get understanding score from pre-fetched data
                    score = understanding_scores.get(question.id)
                    if score is not None:
                        subtopic_performance[subtopic]['avg_understanding'].append(score)
                        if score <= 2:
                            subtopic_performance[subtopic]['low_understanding'] += 1
        
        # Identify subtopics that need more questions
        for subtopic_name, perf in subtopic_performance.items():
            avg_score = (
                sum(perf['avg_understanding']) / len(perf['avg_understanding'])
                if perf['avg_understanding'] else 5.0
            )
            if perf['low_understanding'] > 0 or perf['incorrect_answers'] > 0 or avg_score < 3.0:
                learning_gaps.append({
                    'subtopic': subtopic_name,
                    'reason': f"Low understanding (avg: {avg_score:.1f}/5) or incorrect answers"
                })
        
        # Also include subtopics that have no questions yet
        subtopics_with_questions = {q.subtopic for q in existing_questions if q.subtopic}
        for subtopic in subtopics:
            if subtopic['name'] not in subtopics_with_questions:
                learning_gaps.append({
                    'subtopic': subtopic['name'],
                    'reason': "No questions yet for this subtopic"
                })
        
        # Format existing questions for context (to avoid duplicates)
        existing_questions_summary = [
            {
                "question": q.question_text,
                "subtopic": q.subtopic,
                "difficulty": q.difficulty
            }
            for q in existing_questions
        ]
        
        # Get generation parameters from config
        qg_config = self.config.get('ai.question_generation', {})
        temperature = qg_config.get('temperature', 0.8)
        max_tokens = qg_config.get('max_tokens', 4000)
        
        # Format knowledge graph as string
        graph_str = json.dumps(knowledge_graph, indent=2)
        existing_questions_str = json.dumps(existing_questions_summary, indent=2)
        learning_gaps_str = json.dumps(learning_gaps, indent=2) if learning_gaps else "None identified"
        
        # Generate enhanced prompt using the template
        prompt = ADDITIONAL_QUESTIONS_PROMPT_TEMPLATE.format(
            count=count,
            topic_name=topic_name,
            knowledge_graph=graph_str,
            existing_questions=existing_questions_str,
            learning_gaps=learning_gaps_str,
            question_output_format=QUESTION_OUTPUT_FORMAT
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
        """Start a quiz for a topic with intelligent question selection.
        
        Questions are prioritized in this order:
        1. Questions that have never been answered
        2. Questions that have been answered incorrectly (most recent answer was wrong)
        3. Questions that have been answered correctly
        
        Args:
            topic_id: ID of the topic to quiz on
            num_questions: Number of questions to include (default from config)
            
        Returns:
            List of questions for the quiz, prioritized by learning needs
        """
        if num_questions is None:
            num_questions = self.config.get_app_config().get('quiz_questions_per_session', 5)
        
        # Get all questions for the topic
        all_questions = self.storage.get_questions_for_topic(topic_id)
        
        if not all_questions:
            raise ValueError(f"No questions found for topic ID {topic_id}")
        
        # If we need all questions or fewer, return them all
        if len(all_questions) <= num_questions:
            return all_questions
        
        # Get answer statistics for intelligent selection
        answer_stats = self.storage.get_question_answer_stats(topic_id)
        
        # Categorize questions by priority
        never_answered = []
        incorrectly_answered = []
        correctly_answered = []
        
        for question in all_questions:
            stats = answer_stats.get(question.id, {})
            has_answers = stats.get('has_answers', False)
            last_correct = stats.get('last_answer_correct')
            
            if not has_answers:
                # Priority 1: Never answered
                never_answered.append(question)
            elif last_correct is False:
                # Priority 2: Most recent answer was incorrect
                incorrectly_answered.append(question)
            else:
                # Priority 3: Most recent answer was correct (or no stats available)
                correctly_answered.append(question)
        
        # Shuffle each category for randomness within priority levels
        random.shuffle(never_answered)
        random.shuffle(incorrectly_answered)
        random.shuffle(correctly_answered)
        
        # Select questions in priority order
        selected_questions = []
        
        # First, add never-answered questions
        remaining = num_questions
        if never_answered:
            take = min(remaining, len(never_answered))
            selected_questions.extend(never_answered[:take])
            remaining -= take
        
        # Then, add incorrectly-answered questions
        if remaining > 0 and incorrectly_answered:
            take = min(remaining, len(incorrectly_answered))
            selected_questions.extend(incorrectly_answered[:take])
            remaining -= take
        
        # Finally, add correctly-answered questions if we still need more
        if remaining > 0 and correctly_answered:
            take = min(remaining, len(correctly_answered))
            selected_questions.extend(correctly_answered[:take])
        
        return selected_questions
    
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
        understanding_score = result.get('understanding_score')
        feedback = result.get('feedback', '')
        
        # Validate and clamp understanding_score to 1-5 range
        if understanding_score is not None:
            understanding_score = max(1, min(5, int(understanding_score)))
        
        # Create answer object
        answer = Answer(
            question_id=question.id,
            user_answer=user_answer,
            is_correct=is_correct,
            understanding_score=understanding_score,
            feedback=feedback,
            timestamp=datetime.now()
        )
        
        # Save answer to database
        answer_id = self.storage.save_answer(answer)
        answer.id = answer_id
        
        # Update knowledge graph
        try:
            # Get topic name for knowledge graph
            topic = self.storage.get_topic(question.topic_id)
            if topic:
                topic_name = topic.name
                
                # Add question node if it doesn't exist
                if not self.knowledge_graph.question_exists(question.id):
                    self.knowledge_graph.add_question_node(question, topic_name)
                
                # Always add answer node
                self.knowledge_graph.add_answer_node(answer, question)
        except Exception as e:
            # Log error but don't fail the grading if knowledge graph update fails
            print(f"Warning: Failed to update knowledge graph: {str(e)}")
        
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
        avg_understanding = sum(a.understanding_score or 0 for a in answers) / total if total > 0 else 0.0
        
        return {
            'total_questions': total,
            'correct_answers': correct,
            'incorrect_answers': total - correct,
            'score': score,
            'average_understanding': avg_understanding
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

