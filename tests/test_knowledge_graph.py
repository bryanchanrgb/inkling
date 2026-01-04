"""Tests for Neo4j knowledge graph operations."""

import pytest
from inkling.knowledge_graph import KnowledgeGraph


@pytest.fixture
def kg():
    """Create a KnowledgeGraph instance for testing."""
    kg_instance = KnowledgeGraph()
    yield kg_instance
    # Cleanup: close connection after test
    kg_instance.close()


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
        kg = KnowledgeGraph()
        
        # Verify connection
        with kg.driver.session() as session:
            result = session.run("RETURN 'connection_test' as test")
            record = result.single()
            assert record['test'] == 'connection_test'
        
        print("✓ Connection verification successful")
        kg.close()
        
    except Exception as e:
        pytest.fail(f"Connection verification failed: {str(e)}. "
                   f"Make sure Neo4j is running at the configured URI and "
                   f"credentials are set in .env file.")

