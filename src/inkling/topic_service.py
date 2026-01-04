"""Topic service for creating topics and knowledge graphs."""

from datetime import datetime
from typing import List, Tuple

from .ai_service import get_ai_service
from .config import get_config
from .knowledge_graph import KnowledgeGraph
from .models import Question, Topic
from .storage import Storage


class TopicService:
    """Service for managing topics and knowledge graphs."""
    
    def __init__(self):
        """Initialize topic service."""
        self.ai_service = get_ai_service()
        self.knowledge_graph = KnowledgeGraph()
        self.storage = Storage()
        self.config = get_config()
    
    def create_topic(self, topic_name: str) -> Tuple[Topic, List[Question]]:
        """Create a new topic with knowledge graph and questions.
        
        Args:
            topic_name: Name of the topic to create
            
        Returns:
            Tuple of (Topic, List[Question])
        """
        # Check if topic already exists
        existing_topic = self.storage.get_topic_by_name(topic_name)
        if existing_topic:
            raise ValueError(f"Topic '{topic_name}' already exists")
        
        # Step 1: Generate knowledge graph structure using AI
        graph_structure = self.ai_service.generate_knowledge_graph(topic_name)
        
        # Step 2: Store knowledge graph in Neo4j
        graph_id = self.knowledge_graph.create_topic_graph(topic_name, graph_structure)
        
        # Step 3: Generate questions using AI
        question_count = self.config.get_app_config().get('default_question_count', 10)
        question_data = self.ai_service.generate_questions(topic_name, graph_structure, count=question_count)
        
        # Step 4: Create topic in database
        topic = Topic(
            name=topic_name,
            description=f"Knowledge graph with {len(graph_structure.get('subtopics', []))} subtopics",
            created_at=datetime.now(),
            knowledge_graph_id=graph_id
        )
        topic_id = self.storage.save_topic(topic)
        topic.id = topic_id
        
        # Step 5: Create questions in database
        questions = []
        for q_data in question_data:
            question = Question(
                topic_id=topic_id,
                question_text=q_data.get('question_text', ''),
                correct_answer=q_data.get('correct_answer', ''),
                subtopic=q_data.get('subtopic'),
                difficulty=q_data.get('difficulty')
            )
            question_id = self.storage.save_question(question)
            question.id = question_id
            questions.append(question)
        
        return topic, questions
    
    def get_topic(self, topic_id: int) -> Topic:
        """Get a topic by ID."""
        topic = self.storage.get_topic(topic_id)
        if not topic:
            raise ValueError(f"Topic with ID {topic_id} not found")
        return topic
    
    def list_topics(self) -> List[Topic]:
        """List all topics."""
        return self.storage.list_topics()
    
    def get_subtopics(self, topic_name: str) -> List[dict]:
        """Get subtopics for a topic."""
        return self.knowledge_graph.get_subtopics(topic_name)
    
    def close(self):
        """Close connections."""
        self.knowledge_graph.close()

