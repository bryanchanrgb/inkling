"""Tests for Neo4j knowledge graph operations (optional Neo4j implementation)."""

from datetime import datetime

import pytest
from inkling.knowledge_graph import Neo4jKnowledgeGraph
from inkling.models import Answer, Question


@pytest.fixture
def kg():
    """Create a Neo4jKnowledgeGraph instance for testing."""
    try:
        kg_instance = Neo4jKnowledgeGraph()
        yield kg_instance
        # Cleanup: close connection after test
        kg_instance.close()
    except ImportError as e:
        pytest.skip(f"Neo4j is not available: {e}")
    except Exception as e:
        pytest.skip(f"Could not connect to Neo4j: {e}")


@pytest.fixture
def test_topic_name():
    """Test topic name for use in tests."""
    return "Test Topic for Knowledge Graph"


@pytest.fixture
def sample_graph_structure():
    """Sample graph structure for testing."""
    return {
        "subtopics": [
            {
                "name": "Subtopic A",
                "description": "First subtopic",
                "prerequisites": [],
                "related": ["Subtopic B"]
            },
            {
                "name": "Subtopic B",
                "description": "Second subtopic",
                "prerequisites": ["Subtopic A"],
                "related": ["Subtopic A"]
            },
            {
                "name": "Subtopic C",
                "description": "Third subtopic",
                "prerequisites": ["Subtopic B"],
                "related": []
            }
        ]
    }


@pytest.fixture
def sample_question():
    """Sample question for testing."""
    return Question(
        id=9999,
        topic_id=1,
        question_text="What is the capital of France?",
        correct_answer="Paris",
        subtopic="Subtopic A",
        difficulty="easy"
    )


@pytest.fixture
def sample_answer(sample_question):
    """Sample answer for testing."""
    return Answer(
        id=8888,
        question_id=sample_question.id,
        user_answer="Paris",
        is_correct=True,
        understanding_score=5,
        feedback="Correct! Paris is the capital of France.",
        timestamp=datetime.now()
    )


def test_neo4j_connection(kg):
    """Test that we can connect to Neo4j instance."""
    try:
        # Try to verify the connection by running a simple query
        with kg.driver.session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            assert record is not None
            assert record['test'] == 1
        print("✓ Successfully connected to Neo4j instance")
    except Exception as e:
        pytest.fail(f"Failed to connect to Neo4j: {str(e)}. "
                   f"Make sure Neo4j is running and credentials are set in .env file.")


def test_create_topic_graph(kg, test_topic_name, sample_graph_structure):
    """Test creating a topic graph in Neo4j."""
    try:
        # Clean up any existing test topic first
        kg.delete_topic_graph(test_topic_name)
        
        # Create the topic graph
        graph_id = kg.create_topic_graph(test_topic_name, sample_graph_structure)
        
        # Verify the graph ID is returned
        assert graph_id == test_topic_name
        
        # Verify the topic was created by querying it
        with kg.driver.session() as session:
            result = session.run(
                "MATCH (t:Topic {name: $name}) RETURN t.name as name",
                name=test_topic_name
            )
            record = result.single()
            assert record is not None
            assert record['name'] == test_topic_name
        
        print(f"✓ Successfully created topic graph: {test_topic_name}")
        
    except Exception as e:
        pytest.fail(f"Failed to create topic graph: {str(e)}")
    finally:
        # Cleanup
        kg.delete_topic_graph(test_topic_name)


def test_get_subtopics(kg, test_topic_name, sample_graph_structure):
    """Test retrieving subtopics for a topic."""
    try:
        # Clean up any existing test topic first
        kg.delete_topic_graph(test_topic_name)
        
        # Create the topic graph
        kg.create_topic_graph(test_topic_name, sample_graph_structure)
        
        # Get subtopics
        subtopics = kg.get_subtopics(test_topic_name)
        
        # Verify we got the expected subtopics
        assert len(subtopics) == 3
        assert all('name' in st for st in subtopics)
        assert all('description' in st for st in subtopics)
        
        # Verify specific subtopics exist
        subtopic_names = [st['name'] for st in subtopics]
        assert "Subtopic A" in subtopic_names
        assert "Subtopic B" in subtopic_names
        assert "Subtopic C" in subtopic_names
        
        print(f"✓ Successfully retrieved {len(subtopics)} subtopics")
        
    except Exception as e:
        pytest.fail(f"Failed to get subtopics: {str(e)}")
    finally:
        # Cleanup
        kg.delete_topic_graph(test_topic_name)


def test_get_prerequisites(kg, test_topic_name, sample_graph_structure):
    """Test retrieving prerequisites for a subtopic."""
    try:
        # Clean up any existing test topic first
        kg.delete_topic_graph(test_topic_name)
        
        # Create the topic graph
        kg.create_topic_graph(test_topic_name, sample_graph_structure)
        
        # Get prerequisites for Subtopic B (should have Subtopic A)
        prerequisites = kg.get_prerequisites("Subtopic B")
        
        # Verify prerequisites
        assert "Subtopic A" in prerequisites
        
        # Get prerequisites for Subtopic C (should have Subtopic B)
        prerequisites_c = kg.get_prerequisites("Subtopic C")
        assert "Subtopic B" in prerequisites_c
        
        # Get prerequisites for Subtopic A (should have none)
        prerequisites_a = kg.get_prerequisites("Subtopic A")
        assert len(prerequisites_a) == 0
        
        print("✓ Successfully retrieved prerequisites")
        
    except Exception as e:
        pytest.fail(f"Failed to get prerequisites: {str(e)}")
    finally:
        # Cleanup
        kg.delete_topic_graph(test_topic_name)


def test_get_related_topics(kg, test_topic_name, sample_graph_structure):
    """Test retrieving related topics for a subtopic."""
    try:
        # Clean up any existing test topic first
        kg.delete_topic_graph(test_topic_name)
        
        # Create the topic graph
        kg.create_topic_graph(test_topic_name, sample_graph_structure)
        
        # Get related topics for Subtopic A (should have Subtopic B)
        related = kg.get_related_topics("Subtopic A")
        assert "Subtopic B" in related
        
        # Get related topics for Subtopic B (should have Subtopic A)
        related_b = kg.get_related_topics("Subtopic B")
        assert "Subtopic A" in related_b
        
        print("✓ Successfully retrieved related topics")
        
    except Exception as e:
        pytest.fail(f"Failed to get related topics: {str(e)}")
    finally:
        # Cleanup
        kg.delete_topic_graph(test_topic_name)


def test_delete_topic_graph(kg, test_topic_name, sample_graph_structure):
    """Test deleting a topic graph."""
    try:
        # Clean up any existing test topic first
        kg.delete_topic_graph(test_topic_name)
        
        # Create the topic graph
        kg.create_topic_graph(test_topic_name, sample_graph_structure)
        
        # Verify it exists
        subtopics_before = kg.get_subtopics(test_topic_name)
        assert len(subtopics_before) > 0
        
        # Delete the topic graph
        kg.delete_topic_graph(test_topic_name)
        
        # Verify it's deleted
        subtopics_after = kg.get_subtopics(test_topic_name)
        assert len(subtopics_after) == 0
        
        # Verify topic node is also deleted
        with kg.driver.session() as session:
            result = session.run(
                "MATCH (t:Topic {name: $name}) RETURN t",
                name=test_topic_name
            )
            record = result.single()
            assert record is None
        
        print("✓ Successfully deleted topic graph")
        
    except Exception as e:
        pytest.fail(f"Failed to delete topic graph: {str(e)}")
    finally:
        # Ensure cleanup
        kg.delete_topic_graph(test_topic_name)


def test_connection_verification():
    """Test that connection verification works independently."""
    try:
        kg = Neo4jKnowledgeGraph()
        
        # Verify connection
        with kg.driver.session() as session:
            result = session.run("RETURN 'connection_test' as test")
            record = result.single()
            assert record['test'] == 'connection_test'
        
        print("✓ Connection verification successful")
        kg.close()
        
    except ImportError as e:
        pytest.skip(f"Neo4j is not available: {e}")
    except Exception as e:
        pytest.skip(f"Could not connect to Neo4j: {e}")


def test_question_exists(kg, test_topic_name, sample_graph_structure, sample_question):
    """Test checking if a question exists in the graph."""
    try:
        # Clean up any existing test data
        kg.delete_topic_graph(test_topic_name)
        
        # Create topic graph first
        kg.create_topic_graph(test_topic_name, sample_graph_structure)
        
        # Question should not exist initially
        assert not kg.question_exists(sample_question.id)
        
        # Add the question
        kg.add_question_node(sample_question, test_topic_name)
        
        # Question should now exist
        assert kg.question_exists(sample_question.id)
        
        print("✓ Successfully verified question_exists method")
        
    except Exception as e:
        pytest.fail(f"Failed to test question_exists: {str(e)}")
    finally:
        # Cleanup
        with kg.driver.session() as session:
            session.run("MATCH (q:Question {question_id: $id}) DETACH DELETE q", id=sample_question.id)
            session.run("MATCH (a:Answer {answer_id: $id}) DETACH DELETE a", id=8888)
        kg.delete_topic_graph(test_topic_name)


def test_add_question_node(kg, test_topic_name, sample_graph_structure, sample_question):
    """Test adding a question node to the knowledge graph."""
    try:
        # Clean up any existing test data
        kg.delete_topic_graph(test_topic_name)
        
        # Create topic graph first
        kg.create_topic_graph(test_topic_name, sample_graph_structure)
        
        # Add question node
        kg.add_question_node(sample_question, test_topic_name)
        
        # Verify question node was created with correct properties
        with kg.driver.session() as session:
            result = session.run(
                """
                MATCH (q:Question {question_id: $question_id})
                RETURN q.question_id as question_id,
                       q.question_text as question_text,
                       q.correct_answer as correct_answer
                """,
                question_id=sample_question.id
            )
            record = result.single()
            assert record is not None
            assert record['question_id'] == sample_question.id
            assert record['question_text'] == sample_question.question_text
            assert record['correct_answer'] == sample_question.correct_answer
        
        # Verify edge to Topic exists
        with kg.driver.session() as session:
            result = session.run(
                """
                MATCH (t:Topic {name: $topic_name})-[:HAS_QUESTION]->(q:Question {question_id: $question_id})
                RETURN count(*) as count
                """,
                topic_name=test_topic_name,
                question_id=sample_question.id
            )
            record = result.single()
            assert record['count'] == 1
        
        # Verify edge to Subtopic exists (since question has a subtopic)
        with kg.driver.session() as session:
            result = session.run(
                """
                MATCH (s:Subtopic {name: $subtopic_name})-[:HAS_QUESTION]->(q:Question {question_id: $question_id})
                RETURN count(*) as count
                """,
                subtopic_name=sample_question.subtopic,
                question_id=sample_question.id
            )
            record = result.single()
            assert record['count'] == 1
        
        print("✓ Successfully added question node with correct properties and relationships")
        
    except Exception as e:
        pytest.fail(f"Failed to add question node: {str(e)}")
    finally:
        # Cleanup
        with kg.driver.session() as session:
            session.run("MATCH (q:Question {question_id: $id}) DETACH DELETE q", id=sample_question.id)
            session.run("MATCH (a:Answer {answer_id: $id}) DETACH DELETE a", id=8888)
        kg.delete_topic_graph(test_topic_name)


def test_add_question_node_no_duplicate(kg, test_topic_name, sample_graph_structure, sample_question):
    """Test that adding the same question twice doesn't create duplicates."""
    try:
        # Clean up any existing test data
        kg.delete_topic_graph(test_topic_name)
        
        # Create topic graph first
        kg.create_topic_graph(test_topic_name, sample_graph_structure)
        
        # Add question node first time
        kg.add_question_node(sample_question, test_topic_name)
        
        # Count question nodes
        with kg.driver.session() as session:
            result = session.run(
                "MATCH (q:Question {question_id: $id}) RETURN count(*) as count",
                id=sample_question.id
            )
            count_before = result.single()['count']
        
        # Try to add the same question again
        kg.add_question_node(sample_question, test_topic_name)
        
        # Count question nodes again
        with kg.driver.session() as session:
            result = session.run(
                "MATCH (q:Question {question_id: $id}) RETURN count(*) as count",
                id=sample_question.id
            )
            count_after = result.single()['count']
        
        # Should still be only one question node
        assert count_before == 1
        assert count_after == 1
        
        print("✓ Successfully prevented duplicate question nodes")
        
    except Exception as e:
        pytest.fail(f"Failed to test duplicate prevention: {str(e)}")
    finally:
        # Cleanup
        with kg.driver.session() as session:
            session.run("MATCH (q:Question {question_id: $id}) DETACH DELETE q", id=sample_question.id)
            session.run("MATCH (a:Answer {answer_id: $id}) DETACH DELETE a", id=8888)
        kg.delete_topic_graph(test_topic_name)


def test_add_answer_node(kg, test_topic_name, sample_graph_structure, sample_question, sample_answer):
    """Test adding an answer node to the knowledge graph."""
    try:
        # Clean up any existing test data
        kg.delete_topic_graph(test_topic_name)
        
        # Create topic graph first
        kg.create_topic_graph(test_topic_name, sample_graph_structure)
        
        # Add answer node (this should also create the question node if it doesn't exist)
        kg.add_answer_node(sample_answer, sample_question)
        
        # Verify answer node was created with correct properties
        with kg.driver.session() as session:
            result = session.run(
                """
                MATCH (a:Answer {answer_id: $answer_id})
                RETURN a.answer_id as answer_id,
                       a.question_id as question_id,
                       a.user_answer as user_answer,
                       a.feedback as feedback
                """,
                answer_id=sample_answer.id
            )
            record = result.single()
            assert record is not None
            assert record['answer_id'] == sample_answer.id
            assert record['question_id'] == sample_answer.question_id
            assert record['user_answer'] == sample_answer.user_answer
            assert record['feedback'] == sample_answer.feedback
        
        # Verify edge from Answer to Question exists
        with kg.driver.session() as session:
            result = session.run(
                """
                MATCH (a:Answer {answer_id: $answer_id})-[:ANSWERS]->(q:Question {question_id: $question_id})
                RETURN count(*) as count
                """,
                answer_id=sample_answer.id,
                question_id=sample_question.id
            )
            record = result.single()
            assert record['count'] == 1
        
        # Verify question node was created (since add_answer_node creates it if missing)
        assert kg.question_exists(sample_question.id)
        
        print("✓ Successfully added answer node with correct properties and relationship")
        
    except Exception as e:
        pytest.fail(f"Failed to add answer node: {str(e)}")
    finally:
        # Cleanup
        with kg.driver.session() as session:
            session.run("MATCH (q:Question {question_id: $id}) DETACH DELETE q", id=sample_question.id)
            session.run("MATCH (a:Answer {answer_id: $id}) DETACH DELETE a", id=sample_answer.id)
        kg.delete_topic_graph(test_topic_name)


def test_add_multiple_answers_to_question(kg, test_topic_name, sample_graph_structure, sample_question):
    """Test that multiple answers can be added to the same question."""
    try:
        # Clean up any existing test data
        kg.delete_topic_graph(test_topic_name)
        
        # Create topic graph first
        kg.create_topic_graph(test_topic_name, sample_graph_structure)
        
        # Add question node first
        kg.add_question_node(sample_question, test_topic_name)
        
        # Create multiple answers
        answer1 = Answer(
            id=8888,
            question_id=sample_question.id,
            user_answer="Paris",
            is_correct=True,
            feedback="Correct!",
            timestamp=datetime.now()
        )
        
        answer2 = Answer(
            id=8889,
            question_id=sample_question.id,
            user_answer="London",
            is_correct=False,
            feedback="Incorrect. The answer is Paris.",
            timestamp=datetime.now()
        )
        
        # Add both answers
        kg.add_answer_node(answer1, sample_question)
        kg.add_answer_node(answer2, sample_question)
        
        # Verify both answer nodes exist
        with kg.driver.session() as session:
            result = session.run(
                """
                MATCH (a:Answer)-[:ANSWERS]->(q:Question {question_id: $question_id})
                RETURN count(*) as count
                """,
                question_id=sample_question.id
            )
            record = result.single()
            assert record['count'] == 2
        
        # Verify both answers are linked to the same question
        with kg.driver.session() as session:
            result = session.run(
                """
                MATCH (a:Answer)-[:ANSWERS]->(q:Question {question_id: $question_id})
                RETURN collect(a.answer_id) as answer_ids
                """,
                question_id=sample_question.id
            )
            record = result.single()
            answer_ids = record['answer_ids']
            assert answer1.id in answer_ids
            assert answer2.id in answer_ids
        
        print("✓ Successfully added multiple answers to the same question")
        
    except Exception as e:
        pytest.fail(f"Failed to add multiple answers: {str(e)}")
    finally:
        # Cleanup
        with kg.driver.session() as session:
            session.run("MATCH (q:Question {question_id: $id}) DETACH DELETE q", id=sample_question.id)
            session.run("MATCH (a:Answer) WHERE a.answer_id IN [8888, 8889] DETACH DELETE a")
        kg.delete_topic_graph(test_topic_name)


def test_add_question_node_without_subtopic(kg, test_topic_name, sample_graph_structure):
    """Test adding a question node that doesn't have a subtopic."""
    try:
        # Clean up any existing test data
        kg.delete_topic_graph(test_topic_name)
        
        # Create topic graph first
        kg.create_topic_graph(test_topic_name, sample_graph_structure)
        
        # Create question without subtopic
        question_no_subtopic = Question(
            id=9998,
            topic_id=1,
            question_text="What is 2+2?",
            correct_answer="4",
            subtopic=None,
            difficulty="easy"
        )
        
        # Add question node
        kg.add_question_node(question_no_subtopic, test_topic_name)
        
        # Verify question node was created
        assert kg.question_exists(question_no_subtopic.id)
        
        # Verify edge to Topic exists
        with kg.driver.session() as session:
            result = session.run(
                """
                MATCH (t:Topic {name: $topic_name})-[:HAS_QUESTION]->(q:Question {question_id: $question_id})
                RETURN count(*) as count
                """,
                topic_name=test_topic_name,
                question_id=question_no_subtopic.id
            )
            record = result.single()
            assert record['count'] == 1
        
        # Verify no edge to Subtopic exists (since question has no subtopic)
        with kg.driver.session() as session:
            result = session.run(
                """
                MATCH (s:Subtopic)-[:HAS_QUESTION]->(q:Question {question_id: $question_id})
                RETURN count(*) as count
                """,
                question_id=question_no_subtopic.id
            )
            record = result.single()
            assert record['count'] == 0
        
        print("✓ Successfully added question node without subtopic")
        
    except Exception as e:
        pytest.fail(f"Failed to add question without subtopic: {str(e)}")
    finally:
        # Cleanup
        with kg.driver.session() as session:
            session.run("MATCH (q:Question {question_id: $id}) DETACH DELETE q", id=9998)
            session.run("MATCH (a:Answer {answer_id: $id}) DETACH DELETE a", id=8888)
        kg.delete_topic_graph(test_topic_name)

