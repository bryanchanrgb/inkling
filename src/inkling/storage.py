"""SQLite storage operations."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .config import get_config
from .models import Answer, Question, Topic


class Storage:
    """Manages SQLite database operations."""
    
    def __init__(self):
        """Initialize database connection."""
        config = get_config()
        storage_config = config.get_storage_config()
        db_path = storage_config.get('database_path', 'data/inkling.db')
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Topics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                knowledge_graph_id TEXT
            )
        """)
        
        # Questions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                subtopic TEXT,
                difficulty TEXT,
                FOREIGN KEY (topic_id) REFERENCES topics(id)
            )
        """)
        
        # Answers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                user_answer TEXT NOT NULL,
                is_correct BOOLEAN NOT NULL,
                confidence_score REAL,
                feedback TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (question_id) REFERENCES questions(id)
            )
        """)
        
        # Quiz sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                score REAL,
                total_questions INTEGER,
                correct_answers INTEGER,
                FOREIGN KEY (topic_id) REFERENCES topics(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_topic(self, topic: Topic) -> int:
        """Save a topic and return its ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if topic.id:
            cursor.execute("""
                UPDATE topics 
                SET name = ?, description = ?, knowledge_graph_id = ?
                WHERE id = ?
            """, (topic.name, topic.description, topic.knowledge_graph_id, topic.id))
            topic_id = topic.id
        else:
            cursor.execute("""
                INSERT INTO topics (name, description, knowledge_graph_id, created_at)
                VALUES (?, ?, ?, ?)
            """, (topic.name, topic.description, topic.knowledge_graph_id, 
                  topic.created_at or datetime.now()))
            topic_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return topic_id
    
    def get_topic(self, topic_id: int) -> Optional[Topic]:
        """Get a topic by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM topics WHERE id = ?", (topic_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Topic(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                knowledge_graph_id=row['knowledge_graph_id']
            )
        return None
    
    def get_topic_by_name(self, name: str) -> Optional[Topic]:
        """Get a topic by name."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM topics WHERE name = ?", (name,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Topic(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                knowledge_graph_id=row['knowledge_graph_id']
            )
        return None
    
    def list_topics(self) -> List[Topic]:
        """List all topics."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM topics ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        return [
            Topic(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                knowledge_graph_id=row['knowledge_graph_id']
            )
            for row in rows
        ]
    
    def save_question(self, question: Question) -> int:
        """Save a question and return its ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if question.id:
            cursor.execute("""
                UPDATE questions 
                SET topic_id = ?, question_text = ?, correct_answer = ?, subtopic = ?, difficulty = ?
                WHERE id = ?
            """, (question.topic_id, question.question_text, question.correct_answer,
                  question.subtopic, question.difficulty, question.id))
            question_id = question.id
        else:
            cursor.execute("""
                INSERT INTO questions (topic_id, question_text, correct_answer, subtopic, difficulty)
                VALUES (?, ?, ?, ?, ?)
            """, (question.topic_id, question.question_text, question.correct_answer,
                  question.subtopic, question.difficulty))
            question_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return question_id
    
    def save_questions(self, questions: List[Question]) -> List[int]:
        """Save multiple questions and return their IDs."""
        return [self.save_question(q) for q in questions]
    
    def get_questions_for_topic(self, topic_id: int) -> List[Question]:
        """Get all questions for a topic."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM questions WHERE topic_id = ?", (topic_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [
            Question(
                id=row['id'],
                topic_id=row['topic_id'],
                question_text=row['question_text'],
                correct_answer=row['correct_answer'],
                subtopic=row['subtopic'],
                difficulty=row['difficulty']
            )
            for row in rows
        ]
    
    def save_answer(self, answer: Answer) -> int:
        """Save an answer and return its ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if answer.id:
            cursor.execute("""
                UPDATE answers 
                SET question_id = ?, user_answer = ?, is_correct = ?, 
                    confidence_score = ?, feedback = ?, timestamp = ?
                WHERE id = ?
            """, (answer.question_id, answer.user_answer, answer.is_correct,
                  answer.confidence_score, answer.feedback, 
                  answer.timestamp or datetime.now(), answer.id))
            answer_id = answer.id
        else:
            cursor.execute("""
                INSERT INTO answers (question_id, user_answer, is_correct, 
                                   confidence_score, feedback, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (answer.question_id, answer.user_answer, answer.is_correct,
                  answer.confidence_score, answer.feedback, 
                  answer.timestamp or datetime.now()))
            answer_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return answer_id
    
    def get_quiz_history(self, topic_id: Optional[int] = None, limit: int = 10) -> List[dict]:
        """Get quiz history."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if topic_id:
            cursor.execute("""
                SELECT a.*, q.question_text, q.correct_answer, t.name as topic_name
                FROM answers a
                JOIN questions q ON a.question_id = q.id
                JOIN topics t ON q.topic_id = t.id
                WHERE t.id = ?
                ORDER BY a.timestamp DESC
                LIMIT ?
            """, (topic_id, limit))
        else:
            cursor.execute("""
                SELECT a.*, q.question_text, q.correct_answer, t.name as topic_name
                FROM answers a
                JOIN questions q ON a.question_id = q.id
                JOIN topics t ON q.topic_id = t.id
                ORDER BY a.timestamp DESC
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

