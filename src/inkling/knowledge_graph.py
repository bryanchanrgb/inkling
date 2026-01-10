"""Knowledge graph operations using SQLite by default, with optional Neo4j support."""

import json
import os
from typing import Any, Dict, List, Optional

try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None  # Neo4j is optional

from .ai_service import get_ai_service
from .config import get_config
from .storage import Storage


# Knowledge graph generation prompts
KNOWLEDGE_GRAPH_SYSTEM_MESSAGE = "You are a knowledge graph generator. Always return valid JSON only."

KNOWLEDGE_GRAPH_PROMPT_TEMPLATE = """Generate a knowledge graph structure for the topic: "{topic_name}".

Create a hierarchical structure with:
1. Main subtopics (3-7 subtopics)
2. Relationships between subtopics (prerequisites, related topics)
3. Brief descriptions for each subtopic

Return a JSON object with this structure:
{{
    "subtopics": [
        {{
            "name": "Subtopic Name",
            "description": "Brief description",
            "prerequisites": ["Other subtopic name"],
            "related": ["Related subtopic name"]
        }}
    ]
}}

Only return the JSON, no additional text."""


def _extract_json_content(content: str) -> str:
    """Extract JSON from response content, removing markdown code blocks if present."""
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    return content


class KnowledgeGraph:
    """Manages knowledge graph operations using SQLite storage."""
    
    def __init__(self):
        """Initialize knowledge graph with SQLite storage."""
        self.ai_service = get_ai_service()
        self.config = get_config()
        self.storage = Storage()
    
    def generate_knowledge_graph_structure(self, topic_name: str) -> Dict[str, Any]:
        """Generate a knowledge graph structure for a topic using AI.
        
        Args:
            topic_name: Name of the topic to generate a knowledge graph for
            
        Returns:
            Dictionary containing the knowledge graph structure with subtopics
        """
        # Get generation parameters from config
        kg_config = self.config.get('ai.knowledge_graph', {})
        temperature = kg_config.get('temperature', 0.7)
        max_tokens = kg_config.get('max_tokens', 2000)
        
        # Generate prompt
        prompt = KNOWLEDGE_GRAPH_PROMPT_TEMPLATE.format(topic_name=topic_name)
        
        # Call AI model
        response = self.ai_service.call_model(
            system_message=KNOWLEDGE_GRAPH_SYSTEM_MESSAGE,
            user_message=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Extract and parse JSON
        content = _extract_json_content(response)
        return json.loads(content)
    
    def close(self):
        """Close any connections (no-op for SQLite)."""
        pass
    
    def create_topic_graph(self, topic_name: str, graph_structure: Dict[str, Any]) -> str:
        """Create a knowledge graph for a topic in SQLite.
        
        Args:
            topic_name: Name of the topic
            graph_structure: Knowledge graph structure dictionary
            
        Returns:
            The graph ID (topic name used as identifier)
        """
        # Get topic from database
        topic = self.storage.get_topic_by_name(topic_name)
        if not topic or not topic.id:
            raise ValueError(f"Topic '{topic_name}' not found in database")
        
        # Save subtopics and relationships to SQLite
        self.storage.save_subtopics(topic.id, graph_structure)
        
        return topic_name
    
    def get_subtopics(self, topic_name: str) -> List[Dict[str, Any]]:
        """Get all subtopics for a topic.
        
        Args:
            topic_name: Name of the topic
            
        Returns:
            List of dictionaries with 'name' and 'description'
        """
        topic = self.storage.get_topic_by_name(topic_name)
        if not topic or not topic.id:
            return []
        
        return self.storage.get_subtopics(topic.id)
    
    def get_related_topics(self, subtopic_name: str, topic_name: Optional[str] = None) -> List[str]:
        """Get topics related to a subtopic.
        
        Args:
            subtopic_name: Name of the subtopic
            topic_name: Optional name of the topic (required if multiple topics have same subtopic name)
            
        Returns:
            List of related subtopic names
        """
        if topic_name:
            topic = self.storage.get_topic_by_name(topic_name)
            if not topic or not topic.id:
                return []
            return self.storage.get_related_topics(topic.id, subtopic_name)
        else:
            # If topic_name not provided, search all topics (less efficient)
            # This maintains backward compatibility but is not ideal
            topics = self.storage.list_topics()
            for topic in topics:
                if topic.id:
                    related = self.storage.get_related_topics(topic.id, subtopic_name)
                    if related:
                        return related
            return []
    
    def get_prerequisites(self, subtopic_name: str, topic_name: Optional[str] = None) -> List[str]:
        """Get prerequisites for a subtopic.
        
        Args:
            subtopic_name: Name of the subtopic
            topic_name: Optional name of the topic (required if multiple topics have same subtopic name)
            
        Returns:
            List of prerequisite subtopic names
        """
        if topic_name:
            topic = self.storage.get_topic_by_name(topic_name)
            if not topic or not topic.id:
                return []
            return self.storage.get_prerequisites(topic.id, subtopic_name)
        else:
            # If topic_name not provided, search all topics (less efficient)
            topics = self.storage.list_topics()
            for topic in topics:
                if topic.id:
                    prerequisites = self.storage.get_prerequisites(topic.id, subtopic_name)
                    if prerequisites:
                        return prerequisites
            return []
    
    def delete_topic_graph(self, topic_name: str) -> None:
        """Delete a topic's knowledge graph (subtopics and relationships).
        
        Args:
            topic_name: Name of the topic
        """
        topic = self.storage.get_topic_by_name(topic_name)
        if topic and topic.id:
            self.storage.delete_topic_graph(topic.id)


class Neo4jKnowledgeGraph:
    """Optional Neo4j knowledge graph operations (not used by default).
    
    This class contains all the Neo4j-specific functionality that was previously
    in the main KnowledgeGraph class. These methods are not called in the default
    flow but can be used if Neo4j integration is needed.
    """
    
    def __init__(self):
        """Initialize Neo4j connection to local instance."""
        if GraphDatabase is None:
            raise ImportError("neo4j package is not installed. Install it with: pip install neo4j")
        
        config = get_config()
        neo4j_config = config.get_neo4j_config()
        
        # Get connection URI (defaults to localhost)
        uri = neo4j_config.get('uri', 'bolt://localhost:7687')
        
        # Get credentials from environment variables
        # dotenv is already loaded in config.py
        username = os.getenv('NEO4J_USERNAME', 'neo4j')
        password = os.getenv('NEO4J_PASSWORD', 'password')
        
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.ai_service = get_ai_service()
        self.config = config
    
    def close(self):
        """Close the Neo4j database connection."""
        self.driver.close()
    
    def create_topic_graph(self, topic_name: str, graph_structure: Dict[str, Any]) -> str:
        """Create a knowledge graph for a topic in Neo4j.
        
        Args:
            topic_name: Name of the topic
            graph_structure: Knowledge graph structure dictionary
            
        Returns:
            The graph ID (topic name used as identifier)
        """
        with self.driver.session() as session:
            # Create main topic node
            result = session.run(
                """
                MERGE (t:Topic {name: $topic_name})
                SET t.created_at = datetime()
                RETURN id(t) as topic_id
                """,
                topic_name=topic_name
            )
            topic_id = result.single()['topic_id']
            
            # Create subtopic nodes and relationships
            subtopics = graph_structure.get('subtopics', [])
            for subtopic_data in subtopics:
                subtopic_name = subtopic_data.get('name')
                description = subtopic_data.get('description', '')
                prerequisites = subtopic_data.get('prerequisites', [])
                related = subtopic_data.get('related', [])
                
                # Create subtopic node
                session.run(
                    """
                    MATCH (t:Topic {name: $topic_name})
                    MERGE (s:Subtopic {name: $subtopic_name})
                    SET s.description = $description
                    MERGE (t)-[:HAS_SUBTOPIC]->(s)
                    """,
                    topic_name=topic_name,
                    subtopic_name=subtopic_name,
                    description=description
                )
                
                # Create prerequisite relationships
                for prereq in prerequisites:
                    session.run(
                        """
                        MATCH (s1:Subtopic {name: $subtopic_name})
                        MATCH (s2:Subtopic {name: $prereq})
                        MERGE (s2)-[:PREREQUISITE]->(s1)
                        """,
                        subtopic_name=subtopic_name,
                        prereq=prereq
                    )
                
                # Create related relationships
                for related_topic in related:
                    session.run(
                        """
                        MATCH (s1:Subtopic {name: $subtopic_name})
                        MATCH (s2:Subtopic {name: $related})
                        MERGE (s1)-[:RELATED_TO]->(s2)
                        """,
                        subtopic_name=subtopic_name,
                        related=related_topic
                    )
            
            return topic_name
    
    def get_subtopics(self, topic_name: str) -> List[Dict[str, Any]]:
        """Get all subtopics for a topic from Neo4j."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (t:Topic {name: $topic_name})-[:HAS_SUBTOPIC]->(s:Subtopic)
                RETURN s.name as name, s.description as description
                ORDER BY s.name
                """,
                topic_name=topic_name
            )
            return [dict(record) for record in result]
    
    def get_related_topics(self, subtopic_name: str) -> List[str]:
        """Get topics related to a subtopic from Neo4j."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (s1:Subtopic {name: $subtopic_name})-[:RELATED_TO]-(s2:Subtopic)
                RETURN DISTINCT s2.name as name
                """,
                subtopic_name=subtopic_name
            )
            return [record['name'] for record in result]
    
    def get_prerequisites(self, subtopic_name: str) -> List[str]:
        """Get prerequisites for a subtopic from Neo4j."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (s1:Subtopic)-[:PREREQUISITE]->(s2:Subtopic {name: $subtopic_name})
                RETURN s1.name as name
                """,
                subtopic_name=subtopic_name
            )
            return [record['name'] for record in result]
    
    def delete_topic_graph(self, topic_name: str) -> None:
        """Delete a topic and all its subtopics and relationships from Neo4j."""
        with self.driver.session() as session:
            session.run(
                """
                MATCH (t:Topic {name: $topic_name})
                OPTIONAL MATCH (t)-[:HAS_SUBTOPIC]->(s:Subtopic)
                DETACH DELETE t, s
                """,
                topic_name=topic_name
            )
    
    def question_exists(self, question_id: int) -> bool:
        """Check if a question node already exists in the Neo4j graph.
        
        Args:
            question_id: The question ID to check
            
        Returns:
            True if the question exists, False otherwise
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (q:Question {question_id: $question_id})
                RETURN q
                LIMIT 1
                """,
                question_id=question_id
            )
            return result.single() is not None
    
    def add_question_node(self, question, topic_name: str) -> None:
        """Add a Question node to the Neo4j knowledge graph.
        
        This method should be called when a user answers a question that doesn't
        already exist in the graph. The node will contain question_id, question_text,
        and correct_answer, with edges to the related Topic and Subtopic.
        
        Args:
            question: Question object with id, question_text, correct_answer, subtopic
            topic_name: Name of the topic this question belongs to
        """
        with self.driver.session() as session:
            # Check if question already exists
            if self.question_exists(question.id):
                return  # Question already in graph, skip
            
            # Create Question node
            session.run(
                """
                MERGE (q:Question {question_id: $question_id})
                SET q.question_text = $question_text,
                    q.correct_answer = $correct_answer
                """,
                question_id=question.id,
                question_text=question.question_text,
                correct_answer=question.correct_answer
            )
            
            # Create edge to Topic
            session.run(
                """
                MATCH (t:Topic {name: $topic_name})
                MATCH (q:Question {question_id: $question_id})
                MERGE (t)-[:HAS_QUESTION]->(q)
                """,
                topic_name=topic_name,
                question_id=question.id
            )
            
            # Create edge to Subtopic if subtopic exists
            if question.subtopic:
                session.run(
                    """
                    MATCH (s:Subtopic {name: $subtopic_name})
                    MATCH (q:Question {question_id: $question_id})
                    MERGE (s)-[:HAS_QUESTION]->(q)
                    """,
                    subtopic_name=question.subtopic,
                    question_id=question.id
                )
    
    def add_answer_node(self, answer, question) -> None:
        """Add an Answer node to the Neo4j knowledge graph.
        
        This method should be called whenever a user answers a question,
        regardless of whether it has been answered before. The node will contain
        answer_id, question_id, user_answer, and feedback, with an edge to the Question.
        
        Args:
            answer: Answer object with id, question_id, user_answer, feedback
            question: Question object with id
        """
        with self.driver.session() as session:
            # Ensure Question node exists (create if it doesn't)
            session.run(
                """
                MERGE (q:Question {question_id: $question_id})
                ON CREATE SET q.question_text = $question_text,
                             q.correct_answer = $correct_answer
                """,
                question_id=question.id,
                question_text=question.question_text,
                correct_answer=question.correct_answer
            )
            
            # Create Answer node
            session.run(
                """
                MERGE (a:Answer {answer_id: $answer_id})
                SET a.question_id = $question_id,
                    a.user_answer = $user_answer,
                    a.feedback = $feedback,
                    a.timestamp = datetime()
                """,
                answer_id=answer.id,
                question_id=answer.question_id,
                user_answer=answer.user_answer,
                feedback=answer.feedback or ""
            )
            
            # Create edge from Answer to Question
            session.run(
                """
                MATCH (a:Answer {answer_id: $answer_id})
                MATCH (q:Question {question_id: $question_id})
                MERGE (a)-[:ANSWERS]->(q)
                """,
                answer_id=answer.id,
                question_id=question.id
            )
