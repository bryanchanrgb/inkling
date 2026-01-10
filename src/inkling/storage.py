"""SQLite storage operations."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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
                understanding_score INTEGER,
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
        
        # Subtopics table for knowledge graph
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subtopics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (topic_id) REFERENCES topics(id),
                UNIQUE(topic_id, name)
            )
        """)
        
        # Subtopic relationships table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subtopic_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subtopic_id INTEGER NOT NULL,
                related_subtopic_id INTEGER NOT NULL,
                relationship_type TEXT NOT NULL,
                FOREIGN KEY (subtopic_id) REFERENCES subtopics(id),
                FOREIGN KEY (related_subtopic_id) REFERENCES subtopics(id),
                CHECK (relationship_type IN ('PREREQUISITE', 'RELATED_TO'))
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_subtopics_topic_id ON subtopics(topic_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_subtopic_relationships_subtopic ON subtopic_relationships(subtopic_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_subtopic_relationships_related ON subtopic_relationships(related_subtopic_id)")
        
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
                    understanding_score = ?, feedback = ?, timestamp = ?
                WHERE id = ?
            """, (answer.question_id, answer.user_answer, answer.is_correct,
                  answer.understanding_score, answer.feedback, 
                  answer.timestamp or datetime.now(), answer.id))
            answer_id = answer.id
        else:
            cursor.execute("""
                INSERT INTO answers (question_id, user_answer, is_correct, 
                                   understanding_score, feedback, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (answer.question_id, answer.user_answer, answer.is_correct,
                  answer.understanding_score, answer.feedback, 
                  answer.timestamp or datetime.now()))
            answer_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return answer_id
    
    def get_question_answer_stats(self, topic_id: int) -> Dict[int, dict]:
        """Get answer statistics for all questions in a topic.
        
        Args:
            topic_id: ID of the topic
            
        Returns:
            Dictionary mapping question_id to stats dict with:
            - has_answers: bool (whether question has been answered)
            - last_answer_correct: Optional[bool] (most recent answer correctness)
            - total_answers: int (total number of answers)
            - correct_answers: int (number of correct answers)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all questions for the topic with their answer statistics in a single query
        # Using window functions to get the most recent answer per question
        cursor.execute("""
            WITH LatestAnswers AS (
                SELECT 
                    question_id,
                    is_correct,
                    ROW_NUMBER() OVER (PARTITION BY question_id ORDER BY timestamp DESC) as rn
                FROM answers
                WHERE question_id IN (SELECT id FROM questions WHERE topic_id = ?)
            ),
            AnswerCounts AS (
                SELECT 
                    question_id,
                    COUNT(*) as total_answers,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_answers
                FROM answers
                WHERE question_id IN (SELECT id FROM questions WHERE topic_id = ?)
                GROUP BY question_id
            )
            SELECT 
                q.id as question_id,
                la.is_correct as last_answer_correct,
                COALESCE(ac.total_answers, 0) as total_answers,
                COALESCE(ac.correct_answers, 0) as correct_answers
            FROM questions q
            LEFT JOIN LatestAnswers la ON q.id = la.question_id AND la.rn = 1
            LEFT JOIN AnswerCounts ac ON q.id = ac.question_id
            WHERE q.topic_id = ?
        """, (topic_id, topic_id, topic_id))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Build stats dictionary
        stats = {}
        for row in rows:
            question_id = row['question_id']
            last_correct = row['last_answer_correct']
            total_answers = row['total_answers']
            
            # SQLite stores booleans as 0/1, convert to Python bool
            last_correct_bool = None
            if last_correct is not None:
                last_correct_bool = bool(last_correct)
            
            stats[question_id] = {
                'has_answers': total_answers > 0,
                'last_answer_correct': last_correct_bool,
                'total_answers': total_answers,
                'correct_answers': row['correct_answers']
            }
        
        return stats
    
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
    
    def save_subtopics(self, topic_id: int, graph_structure: dict) -> None:
        """Save subtopics and relationships from a knowledge graph structure.
        
        Args:
            topic_id: ID of the topic
            graph_structure: Dictionary with 'subtopics' list, each containing:
                - name: str
                - description: str (optional)
                - prerequisites: List[str] (optional)
                - related: List[str] (optional)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        subtopics = graph_structure.get('subtopics', [])
        
        # First, create a mapping of subtopic names to their IDs
        subtopic_name_to_id = {}
        
        for subtopic_data in subtopics:
            subtopic_name = subtopic_data.get('name')
            description = subtopic_data.get('description', '')
            
            # Insert or update subtopic
            cursor.execute("""
                INSERT INTO subtopics (topic_id, name, description)
                VALUES (?, ?, ?)
                ON CONFLICT(topic_id, name) DO UPDATE SET
                    description = excluded.description
            """, (topic_id, subtopic_name, description))
            
            # Get the subtopic ID
            cursor.execute("""
                SELECT id FROM subtopics WHERE topic_id = ? AND name = ?
            """, (topic_id, subtopic_name))
            result = cursor.fetchone()
            if result:
                subtopic_name_to_id[subtopic_name] = result[0]
        
        # Now create relationships
        for subtopic_data in subtopics:
            subtopic_name = subtopic_data.get('name')
            subtopic_id = subtopic_name_to_id.get(subtopic_name)
            
            if not subtopic_id:
                continue
            
            # Create prerequisite relationships
            prerequisites = subtopic_data.get('prerequisites', [])
            for prereq_name in prerequisites:
                prereq_id = subtopic_name_to_id.get(prereq_name)
                if prereq_id and prereq_id != subtopic_id:
                    # Prerequisite means: prereq -> subtopic (prereq is prerequisite FOR subtopic)
                    cursor.execute("""
                        INSERT INTO subtopic_relationships (subtopic_id, related_subtopic_id, relationship_type)
                        VALUES (?, ?, 'PREREQUISITE')
                        ON CONFLICT DO NOTHING
                    """, (prereq_id, subtopic_id))
            
            # Create related relationships (bidirectional)
            related = subtopic_data.get('related', [])
            for related_name in related:
                related_id = subtopic_name_to_id.get(related_name)
                if related_id and related_id != subtopic_id:
                    # Related is bidirectional, but we'll store it once
                    cursor.execute("""
                        INSERT INTO subtopic_relationships (subtopic_id, related_subtopic_id, relationship_type)
                        VALUES (?, ?, 'RELATED_TO')
                        ON CONFLICT DO NOTHING
                    """, (subtopic_id, related_id))
        
        conn.commit()
        conn.close()
    
    def get_subtopics(self, topic_id: int) -> List[Dict[str, Any]]:
        """Get all subtopics for a topic.
        
        Args:
            topic_id: ID of the topic
            
        Returns:
            List of dictionaries with 'name' and 'description'
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, description
            FROM subtopics
            WHERE topic_id = ?
            ORDER BY name
        """, (topic_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{'name': row['name'], 'description': row['description']} for row in rows]
    
    def get_related_topics(self, topic_id: int, subtopic_name: str) -> List[str]:
        """Get topics related to a subtopic.
        
        Args:
            topic_id: ID of the topic
            subtopic_name: Name of the subtopic
            
        Returns:
            List of related subtopic names
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get the subtopic ID
        cursor.execute("""
            SELECT id FROM subtopics WHERE topic_id = ? AND name = ?
        """, (topic_id, subtopic_name))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return []
        
        subtopic_id = result[0]
        
        # Get related subtopics (both directions)
        cursor.execute("""
            SELECT DISTINCT s.name
            FROM subtopics s
            JOIN subtopic_relationships sr ON (
                (sr.subtopic_id = ? AND sr.related_subtopic_id = s.id) OR
                (sr.related_subtopic_id = ? AND sr.subtopic_id = s.id)
            )
            WHERE sr.relationship_type = 'RELATED_TO'
            AND s.topic_id = ?
        """, (subtopic_id, subtopic_id, topic_id))
        
        related = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return related
    
    def get_prerequisites(self, topic_id: int, subtopic_name: str) -> List[str]:
        """Get prerequisites for a subtopic.
        
        Args:
            topic_id: ID of the topic
            subtopic_name: Name of the subtopic
            
        Returns:
            List of prerequisite subtopic names
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get the subtopic ID
        cursor.execute("""
            SELECT id FROM subtopics WHERE topic_id = ? AND name = ?
        """, (topic_id, subtopic_name))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return []
        
        subtopic_id = result[0]
        
        # Get prerequisites (prerequisite -> subtopic means subtopic requires prerequisite)
        cursor.execute("""
            SELECT s.name
            FROM subtopics s
            JOIN subtopic_relationships sr ON sr.subtopic_id = s.id
            WHERE sr.related_subtopic_id = ?
            AND sr.relationship_type = 'PREREQUISITE'
            AND s.topic_id = ?
        """, (subtopic_id, topic_id))
        
        prerequisites = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return prerequisites
    
    def delete_topic_graph(self, topic_id: int) -> None:
        """Delete all subtopics and relationships for a topic.
        
        Args:
            topic_id: ID of the topic
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all subtopic IDs for this topic
        cursor.execute("SELECT id FROM subtopics WHERE topic_id = ?", (topic_id,))
        subtopic_ids = [row[0] for row in cursor.fetchall()]
        
        if subtopic_ids:
            placeholders = ','.join('?' * len(subtopic_ids))
            # Delete relationships
            cursor.execute(f"""
                DELETE FROM subtopic_relationships
                WHERE subtopic_id IN ({placeholders}) OR related_subtopic_id IN ({placeholders})
            """, subtopic_ids + subtopic_ids)
            
            # Delete subtopics
            cursor.execute(f"""
                DELETE FROM subtopics WHERE id IN ({placeholders})
            """, subtopic_ids)
        
        conn.commit()
        conn.close()

