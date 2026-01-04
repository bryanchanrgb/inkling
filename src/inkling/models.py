"""Data models for the learning application."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Topic:
    """Represents a learning topic."""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    knowledge_graph_id: Optional[str] = None


@dataclass
class Question:
    """Represents a quiz question."""
    id: Optional[int] = None
    topic_id: int = 0
    question_text: str = ""
    correct_answer: str = ""
    subtopic: Optional[str] = None
    difficulty: Optional[str] = None


@dataclass
class Answer:
    """Represents a user's answer to a question."""
    id: Optional[int] = None
    question_id: int = 0
    user_answer: str = ""
    is_correct: bool = False
    understanding_score: Optional[int] = None  # 1-5 scale: 1=nonexistent/incorrect, 2=some understanding, 3=partial, 4=correct with gaps, 5=perfect
    feedback: Optional[str] = None
    timestamp: Optional[datetime] = None

