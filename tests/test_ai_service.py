"""Tests for AI service providers."""

import pytest
from inkling.ai_service import get_ai_service


def test_ai_service_initialization_and_connection():
    """Test that AI service can be initialized and can reach the AI model."""
    # Get the AI service based on config
    ai_service = get_ai_service()
    
    # Verify the service was initialized
    assert ai_service is not None
    
    # Make a dummy call to verify the AI model can be reached
    try:
        # Call the generic call_model method with a simple test
        response = ai_service.call_model(
            system_message="You are a helpful assistant.",
            user_message="Say 'Hello, world!' and nothing else.",
            temperature=0.0
        )
        
        # Verify we got a response
        print(response)
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        
        print(f"✓ Successfully connected to AI model. Response: {response[:50]}...")
        
    except Exception as e:
        pytest.fail(f"Failed to connect to AI model: {str(e)}")

