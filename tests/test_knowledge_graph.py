"""Tests for SQLite-based knowledge graph operations (default implementation)."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from inkling.knowledge_graph import KnowledgeGraph
from inkling.models import Topic
from inkling.storage import Storage


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    # Cleanup: delete the temporary database file
    try:
        Path(db_path).unlink(missing_ok=True)
    except Exception:
        pass


@pytest.fixture
def storage_with_temp_db(temp_db):
    """Create a Storage instance with a temporary database."""
    with patch('inkling.storage.get_config') as mock_get_config:
        mock_config = mock_get_config.return_value
        mock_config.get_storage_config.return_value = {'database_path': temp_db}
        
        storage = Storage()
        yield storage


@pytest.fixture
def kg(temp_db):
    """Create a KnowledgeGraph instance with a temporary database."""
    from unittest.mock import MagicMock
    
    # Create a shared mock config object
    mock_config = MagicMock()
    mock_config.get_storage_config.return_value = {'database_path': temp_db}
    mock_config.get.return_value = {}
    mock_config.get_ai_config.return_value = {}
    
    # Create a mock AI service
    mock_ai_service = MagicMock()
    
    # Patch get_config in all the places it's used
    with patch('inkling.config.get_config', return_value=mock_config), \
         patch('inkling.storage.get_config', return_value=mock_config), \
         patch('inkling.knowledge_graph.get_config', return_value=mock_config), \
         patch('inkling.knowledge_graph.get_ai_service', return_value=mock_ai_service):
        
        kg_instance = KnowledgeGraph()
        yield kg_instance
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


@pytest.fixture
def test_topic(storage_with_temp_db, test_topic_name):
    """Create a test topic in the database."""
    topic = Topic(
        name=test_topic_name,
        description="Test topic description",
        created_at=datetime.now(),
        knowledge_graph_id=None
    )
    topic_id = storage_with_temp_db.save_topic(topic)
    topic.id = topic_id
    yield topic
    
    # Cleanup: delete the topic and its graph
    if topic.id:
        storage_with_temp_db.delete_topic_graph(topic.id)
        # Note: We can't easily delete the topic itself without direct SQL access,
        # but that's okay for testing purposes


def test_create_topic_graph(kg, storage_with_temp_db, test_topic_name, sample_graph_structure):
    """Test creating a topic graph in SQLite."""
    # Create topic first (required before creating graph)
    topic = Topic(
        name=test_topic_name,
        description="Test topic",
        created_at=datetime.now()
    )
    topic_id = storage_with_temp_db.save_topic(topic)
    topic.id = topic_id
    
    try:
        # Create the topic graph
        graph_id = kg.create_topic_graph(test_topic_name, sample_graph_structure)
        
        # Verify the graph ID is returned (should be topic name)
        assert graph_id == test_topic_name
        
        # Verify subtopics were saved
        subtopics = storage_with_temp_db.get_subtopics(topic_id)
        assert len(subtopics) == 3
        
        subtopic_names = [st['name'] for st in subtopics]
        assert "Subtopic A" in subtopic_names
        assert "Subtopic B" in subtopic_names
        assert "Subtopic C" in subtopic_names
        
        print(f"✓ Successfully created topic graph: {test_topic_name}")
        
    finally:
        # Cleanup
        storage_with_temp_db.delete_topic_graph(topic_id)


def test_create_topic_graph_topic_not_found(kg, sample_graph_structure):
    """Test that creating a graph for non-existent topic raises an error."""
    with pytest.raises(ValueError, match="Topic 'NonExistentTopic' not found"):
        kg.create_topic_graph("NonExistentTopic", sample_graph_structure)


def test_get_subtopics(kg, storage_with_temp_db, test_topic_name, sample_graph_structure):
    """Test retrieving subtopics for a topic."""
    # Create topic first
    topic = Topic(
        name=test_topic_name,
        description="Test topic",
        created_at=datetime.now()
    )
    topic_id = storage_with_temp_db.save_topic(topic)
    topic.id = topic_id
    
    try:
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
        
        # Verify descriptions
        subtopic_dict = {st['name']: st['description'] for st in subtopics}
        assert subtopic_dict["Subtopic A"] == "First subtopic"
        assert subtopic_dict["Subtopic B"] == "Second subtopic"
        assert subtopic_dict["Subtopic C"] == "Third subtopic"
        
        print(f"✓ Successfully retrieved {len(subtopics)} subtopics")
        
    finally:
        # Cleanup
        storage_with_temp_db.delete_topic_graph(topic_id)


def test_get_subtopics_nonexistent_topic(kg):
    """Test retrieving subtopics for a non-existent topic."""
    subtopics = kg.get_subtopics("NonExistentTopic")
    assert subtopics == []


def test_get_prerequisites(kg, storage_with_temp_db, test_topic_name, sample_graph_structure):
    """Test retrieving prerequisites for a subtopic."""
    # Create topic first
    topic = Topic(
        name=test_topic_name,
        description="Test topic",
        created_at=datetime.now()
    )
    topic_id = storage_with_temp_db.save_topic(topic)
    topic.id = topic_id
    
    try:
        # Create the topic graph
        kg.create_topic_graph(test_topic_name, sample_graph_structure)
        
        # Get prerequisites for Subtopic B (should have Subtopic A)
        prerequisites = kg.get_prerequisites("Subtopic B", topic_name=test_topic_name)
        assert "Subtopic A" in prerequisites
        
        # Get prerequisites for Subtopic C (should have Subtopic B)
        prerequisites_c = kg.get_prerequisites("Subtopic C", topic_name=test_topic_name)
        assert "Subtopic B" in prerequisites_c
        
        # Get prerequisites for Subtopic A (should have none)
        prerequisites_a = kg.get_prerequisites("Subtopic A", topic_name=test_topic_name)
        assert len(prerequisites_a) == 0
        
        print("✓ Successfully retrieved prerequisites")
        
    finally:
        # Cleanup
        storage_with_temp_db.delete_topic_graph(topic_id)


def test_get_prerequisites_without_topic_name(kg, storage_with_temp_db, test_topic_name, sample_graph_structure):
    """Test retrieving prerequisites without specifying topic name."""
    # Create topic first
    topic = Topic(
        name=test_topic_name,
        description="Test topic",
        created_at=datetime.now()
    )
    topic_id = storage_with_temp_db.save_topic(topic)
    topic.id = topic_id
    
    try:
        # Create the topic graph
        kg.create_topic_graph(test_topic_name, sample_graph_structure)
        
        # Get prerequisites without topic_name (searches all topics)
        prerequisites = kg.get_prerequisites("Subtopic B")
        assert "Subtopic A" in prerequisites
        
        print("✓ Successfully retrieved prerequisites without topic name")
        
    finally:
        # Cleanup
        storage_with_temp_db.delete_topic_graph(topic_id)


def test_get_related_topics(kg, storage_with_temp_db, test_topic_name, sample_graph_structure):
    """Test retrieving related topics for a subtopic."""
    # Create topic first
    topic = Topic(
        name=test_topic_name,
        description="Test topic",
        created_at=datetime.now()
    )
    topic_id = storage_with_temp_db.save_topic(topic)
    topic.id = topic_id
    
    try:
        # Create the topic graph
        kg.create_topic_graph(test_topic_name, sample_graph_structure)
        
        # Get related topics for Subtopic A (should have Subtopic B)
        related = kg.get_related_topics("Subtopic A", topic_name=test_topic_name)
        assert "Subtopic B" in related
        
        # Get related topics for Subtopic B (should have Subtopic A)
        related_b = kg.get_related_topics("Subtopic B", topic_name=test_topic_name)
        assert "Subtopic A" in related_b
        
        # Get related topics for Subtopic C (should have none)
        related_c = kg.get_related_topics("Subtopic C", topic_name=test_topic_name)
        assert len(related_c) == 0
        
        print("✓ Successfully retrieved related topics")
        
    finally:
        # Cleanup
        storage_with_temp_db.delete_topic_graph(topic_id)


def test_get_related_topics_without_topic_name(kg, storage_with_temp_db, test_topic_name, sample_graph_structure):
    """Test retrieving related topics without specifying topic name."""
    # Create topic first
    topic = Topic(
        name=test_topic_name,
        description="Test topic",
        created_at=datetime.now()
    )
    topic_id = storage_with_temp_db.save_topic(topic)
    topic.id = topic_id
    
    try:
        # Create the topic graph
        kg.create_topic_graph(test_topic_name, sample_graph_structure)
        
        # Get related topics without topic_name (searches all topics)
        related = kg.get_related_topics("Subtopic A")
        assert "Subtopic B" in related
        
        print("✓ Successfully retrieved related topics without topic name")
        
    finally:
        # Cleanup
        storage_with_temp_db.delete_topic_graph(topic_id)


def test_delete_topic_graph(kg, storage_with_temp_db, test_topic_name, sample_graph_structure):
    """Test deleting a topic graph."""
    # Create topic first
    topic = Topic(
        name=test_topic_name,
        description="Test topic",
        created_at=datetime.now()
    )
    topic_id = storage_with_temp_db.save_topic(topic)
    topic.id = topic_id
    
    try:
        # Create the topic graph
        kg.create_topic_graph(test_topic_name, sample_graph_structure)
        
        # Verify it exists
        subtopics_before = kg.get_subtopics(test_topic_name)
        assert len(subtopics_before) == 3
        
        # Delete the topic graph
        kg.delete_topic_graph(test_topic_name)
        
        # Verify it's deleted
        subtopics_after = kg.get_subtopics(test_topic_name)
        assert len(subtopics_after) == 0
        
        print("✓ Successfully deleted topic graph")
        
    finally:
        # Ensure cleanup (in case deletion failed)
        storage_with_temp_db.delete_topic_graph(topic_id)


def test_delete_topic_graph_nonexistent(kg):
    """Test deleting a graph for a non-existent topic (should not raise error)."""
    # Should not raise an error, just do nothing
    kg.delete_topic_graph("NonExistentTopic")


def test_generate_knowledge_graph_structure_mocked(kg):
    """Test generating knowledge graph structure (with mocked AI service)."""
    # Mock the AI service to return a predictable structure
    mock_structure = {
        "subtopics": [
            {
                "name": "Mock Subtopic 1",
                "description": "First mock subtopic",
                "prerequisites": [],
                "related": ["Mock Subtopic 2"]
            },
            {
                "name": "Mock Subtopic 2",
                "description": "Second mock subtopic",
                "prerequisites": ["Mock Subtopic 1"],
                "related": []
            }
        ]
    }
    
    with patch.object(kg.ai_service, 'call_model') as mock_call_model:
        import json
        mock_call_model.return_value = json.dumps(mock_structure)
        
        result = kg.generate_knowledge_graph_structure("Test Topic")
        
        assert result == mock_structure
        assert 'subtopics' in result
        assert len(result['subtopics']) == 2
        
        # Verify the AI service was called
        mock_call_model.assert_called_once()
        call_args = mock_call_model.call_args
        assert "Test Topic" in call_args[1]['user_message'] or "Test Topic" in call_args[0][1]
        
        print("✓ Successfully generated knowledge graph structure")


def test_complete_workflow(kg, storage_with_temp_db, test_topic_name):
    """Test complete workflow: generate structure, create graph, query it."""
    # Create topic first
    topic = Topic(
        name=test_topic_name,
        description="Test topic",
        created_at=datetime.now()
    )
    topic_id = storage_with_temp_db.save_topic(topic)
    topic.id = topic_id
    
    try:
        # Mock the AI service for structure generation
        mock_structure = {
            "subtopics": [
                {
                    "name": "Workflow Subtopic",
                    "description": "Testing complete workflow",
                    "prerequisites": [],
                    "related": []
                }
            ]
        }
        
        with patch.object(kg.ai_service, 'call_model') as mock_call_model:
            import json
            mock_call_model.return_value = json.dumps(mock_structure)
            
            # Generate structure
            structure = kg.generate_knowledge_graph_structure(test_topic_name)
            assert structure == mock_structure
        
        # Create graph
        graph_id = kg.create_topic_graph(test_topic_name, mock_structure)
        assert graph_id == test_topic_name
        
        # Query subtopics
        subtopics = kg.get_subtopics(test_topic_name)
        assert len(subtopics) == 1
        assert subtopics[0]['name'] == "Workflow Subtopic"
        
        # Query prerequisites and related (should be empty)
        prerequisites = kg.get_prerequisites("Workflow Subtopic", topic_name=test_topic_name)
        assert len(prerequisites) == 0
        
        related = kg.get_related_topics("Workflow Subtopic", topic_name=test_topic_name)
        assert len(related) == 0
        
        print("✓ Complete workflow test passed")
        
    finally:
        # Cleanup
        storage_with_temp_db.delete_topic_graph(topic_id)

