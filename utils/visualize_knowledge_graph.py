"""Visualize the current knowledge graph from Neo4j.

This script displays the knowledge graph structure including topics, subtopics,
questions, and answers in a readable format.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Set

# Add src to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from neo4j import GraphDatabase

from inkling.config import get_config

# Load environment variables
load_dotenv()


class KnowledgeGraphVisualizer:
    """Visualizes the Neo4j knowledge graph."""
    
    def __init__(self):
        """Initialize Neo4j connection."""
        config = get_config()
        neo4j_config = config.get_neo4j_config()
        
        uri = neo4j_config.get('uri', 'bolt://localhost:7687')
        username = os.getenv('NEO4J_USERNAME', 'neo4j')
        password = os.getenv('NEO4J_PASSWORD', 'password')
        
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
    
    def close(self):
        """Close the database connection."""
        self.driver.close()
    
    def get_all_topics(self) -> List[Dict]:
        """Get all topics from the graph."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Topic)
                RETURN t.name as name
                ORDER BY t.name
            """)
            return [dict(record) for record in result]
    
    def get_topic_structure(self, topic_name: str) -> Dict:
        """Get complete structure for a topic."""
        with self.driver.session() as session:
            # Get subtopics
            subtopics_result = session.run("""
                MATCH (t:Topic {name: $topic_name})-[:HAS_SUBTOPIC]->(s:Subtopic)
                RETURN s.name as name, s.description as description
                ORDER BY s.name
            """, topic_name=topic_name)
            subtopics = [dict(record) for record in subtopics_result]
            
            # Get questions
            questions_result = session.run("""
                MATCH (t:Topic {name: $topic_name})-[:HAS_QUESTION]->(q:Question)
                RETURN q.question_id as question_id, 
                       q.question_text as question_text,
                       q.correct_answer as correct_answer
                ORDER BY q.question_id
            """, topic_name=topic_name)
            questions = [dict(record) for record in questions_result]
            
            # Get prerequisites for each subtopic
            for subtopic in subtopics:
                prereq_result = session.run("""
                    MATCH (s1:Subtopic)-[:PREREQUISITE]->(s2:Subtopic {name: $name})
                    RETURN s1.name as name
                """, name=subtopic['name'])
                subtopic['prerequisites'] = [record['name'] for record in prereq_result]
                
                related_result = session.run("""
                    MATCH (s1:Subtopic {name: $name})-[:RELATED_TO]-(s2:Subtopic)
                    RETURN DISTINCT s2.name as name
                """, name=subtopic['name'])
                subtopic['related'] = [record['name'] for record in related_result]
            
            # Get answer counts for questions
            for question in questions:
                answer_count_result = session.run("""
                    MATCH (a:Answer)-[:ANSWERS]->(q:Question {question_id: $question_id})
                    RETURN count(a) as count
                """, question_id=question['question_id'])
                question['answer_count'] = answer_count_result.single()['count']
            
            return {
                'topic': topic_name,
                'subtopics': subtopics,
                'questions': questions
            }
    
    def visualize_topic(self, topic_name: str) -> None:
        """Visualize a single topic's structure."""
        structure = self.get_topic_structure(topic_name)
        
        print(f"\n{'='*70}")
        print(f"Topic: {structure['topic']}")
        print(f"{'='*70}\n")
        
        # Display subtopics
        if structure['subtopics']:
            print("Subtopics:")
            print("-" * 70)
            for i, subtopic in enumerate(structure['subtopics'], 1):
                print(f"  {i}. {subtopic['name']}")
                if subtopic.get('description'):
                    print(f"     Description: {subtopic['description']}")
                if subtopic.get('prerequisites'):
                    print(f"     Prerequisites: {', '.join(subtopic['prerequisites'])}")
                if subtopic.get('related'):
                    print(f"     Related to: {', '.join(subtopic['related'])}")
                print()
        else:
            print("No subtopics found.\n")
        
        # Display questions
        if structure['questions']:
            print("Questions:")
            print("-" * 70)
            for i, question in enumerate(structure['questions'], 1):
                print(f"  {i}. [ID: {question['question_id']}]")
                print(f"     Q: {question['question_text'][:60]}...")
                print(f"     A: {question['correct_answer'][:60]}...")
                print(f"     Answers: {question['answer_count']}")
                print()
        else:
            print("No questions found.\n")
    
    def visualize_all(self) -> None:
        """Visualize all topics in the knowledge graph."""
        topics = self.get_all_topics()
        
        if not topics:
            print("No topics found in the knowledge graph.")
            return
        
        print(f"\n{'='*70}")
        print(f"Knowledge Graph Visualization")
        print(f"Total Topics: {len(topics)}")
        print(f"{'='*70}\n")
        
        for topic in topics:
            self.visualize_topic(topic['name'])
            print()
    
    def get_statistics(self) -> Dict:
        """Get overall statistics about the knowledge graph."""
        with self.driver.session() as session:
            stats = {}
            
            # Count nodes
            result = session.run("MATCH (t:Topic) RETURN count(t) as count")
            stats['topics'] = result.single()['count']
            
            result = session.run("MATCH (s:Subtopic) RETURN count(s) as count")
            stats['subtopics'] = result.single()['count']
            
            result = session.run("MATCH (q:Question) RETURN count(q) as count")
            stats['questions'] = result.single()['count']
            
            result = session.run("MATCH (a:Answer) RETURN count(a) as count")
            stats['answers'] = result.single()['count']
            
            # Count relationships
            result = session.run("MATCH ()-[r:HAS_SUBTOPIC]->() RETURN count(r) as count")
            stats['has_subtopic_rels'] = result.single()['count']
            
            result = session.run("MATCH ()-[r:PREREQUISITE]->() RETURN count(r) as count")
            stats['prerequisite_rels'] = result.single()['count']
            
            result = session.run("MATCH ()-[r:RELATED_TO]->() RETURN count(r) as count")
            stats['related_rels'] = result.single()['count']
            
            result = session.run("MATCH ()-[r:HAS_QUESTION]->() RETURN count(r) as count")
            stats['has_question_rels'] = result.single()['count']
            
            result = session.run("MATCH ()-[r:ANSWERS]->() RETURN count(r) as count")
            stats['answers_rels'] = result.single()['count']
            
            return stats
    
    def print_statistics(self) -> None:
        """Print overall statistics."""
        stats = self.get_statistics()
        
        print(f"\n{'='*70}")
        print("Knowledge Graph Statistics")
        print(f"{'='*70}\n")
        
        print("Nodes:")
        print(f"  Topics:        {stats['topics']}")
        print(f"  Subtopics:     {stats['subtopics']}")
        print(f"  Questions:     {stats['questions']}")
        print(f"  Answers:       {stats['answers']}")
        print()
        
        print("Relationships:")
        print(f"  HAS_SUBTOPIC:  {stats['has_subtopic_rels']}")
        print(f"  PREREQUISITE:  {stats['prerequisite_rels']}")
        print(f"  RELATED_TO:    {stats['related_rels']}")
        print(f"  HAS_QUESTION:  {stats['has_question_rels']}")
        print(f"  ANSWERS:       {stats['answers_rels']}")
        print()


def main():
    """Main entry point for visualization."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Visualize the knowledge graph')
    parser.add_argument(
        '--topic',
        type=str,
        help='Visualize a specific topic (if not provided, shows all topics)'
    )
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Show only statistics, not the full graph structure'
    )
    
    args = parser.parse_args()
    
    try:
        visualizer = KnowledgeGraphVisualizer()
        
        if args.stats_only:
            visualizer.print_statistics()
        elif args.topic:
            visualizer.visualize_topic(args.topic)
            visualizer.print_statistics()
        else:
            visualizer.visualize_all()
            visualizer.print_statistics()
        
        visualizer.close()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nMake sure:")
        print("  - Neo4j is running")
        print("  - NEO4J_USERNAME and NEO4J_PASSWORD are set in .env file")
        print("  - The connection URI in config.yaml is correct")
        sys.exit(1)


if __name__ == "__main__":
    main()

