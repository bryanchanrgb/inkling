"""Neo4j knowledge graph operations."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase

from .config import get_config


class KnowledgeGraph:
    """Manages Neo4j knowledge graph operations."""
    
    def __init__(self):
        """Initialize Neo4j connection."""
        config = get_config()
        neo4j_config = config.get_neo4j_config()
        
        if neo4j_config.get('embedded', False):
            # For embedded mode, we'll use a local database
            data_dir = Path(neo4j_config.get('data_directory', 'data/neo4j'))
            data_dir.mkdir(parents=True, exist_ok=True)
            # Note: Embedded Neo4j requires Java and specific setup
            # For now, we'll use a regular connection to a local instance
            uri = neo4j_config.get('uri', 'bolt://localhost:7687')
        else:
            uri = neo4j_config.get('uri', 'bolt://localhost:7687')
        
        username = neo4j_config.get('username', 'neo4j')
        password = neo4j_config.get('password', 'password')
        
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
    
    def close(self):
        """Close the database connection."""
        self.driver.close()
    
    def create_topic_graph(self, topic_name: str, graph_structure: Dict[str, Any]) -> str:
        """Create a knowledge graph for a topic.
        
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
        """Get all subtopics for a topic."""
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
        """Get topics related to a subtopic."""
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
        """Get prerequisites for a subtopic."""
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
        """Delete a topic and all its subtopics and relationships."""
        with self.driver.session() as session:
            session.run(
                """
                MATCH (t:Topic {name: $topic_name})
                OPTIONAL MATCH (t)-[:HAS_SUBTOPIC]->(s:Subtopic)
                DETACH DELETE t, s
                """,
                topic_name=topic_name
            )

