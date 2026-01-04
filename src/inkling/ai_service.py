"""AI service with support for multiple providers."""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from anthropic import Anthropic
from openai import OpenAI

from .config import get_config


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def generate_knowledge_graph(self, topic_name: str) -> Dict[str, Any]:
        """Generate a knowledge graph structure for a topic."""
        pass
    
    @abstractmethod
    def generate_questions(self, topic_name: str, knowledge_graph: Dict[str, Any], count: int = 10) -> List[Dict[str, Any]]:
        """Generate questions based on a knowledge graph."""
        pass
    
    @abstractmethod
    def grade_answer(self, question: str, correct_answer: str, user_answer: str) -> Tuple[bool, float, str]:
        """Grade a user's answer.
        
        Returns:
            Tuple of (is_correct, confidence_score, feedback)
        """
        pass


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenAI provider."""
        api_key = config.get('api_key')
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        self.client = OpenAI(api_key=api_key)
        self.model = config.get('model', 'gpt-4')
    
    def generate_knowledge_graph(self, topic_name: str) -> Dict[str, Any]:
        """Generate a knowledge graph structure for a topic."""
        prompt = f"""Generate a knowledge graph structure for the topic: "{topic_name}".

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

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a knowledge graph generator. Always return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        content = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        return json.loads(content)
    
    def generate_questions(self, topic_name: str, knowledge_graph: Dict[str, Any], count: int = 10) -> List[Dict[str, Any]]:
        """Generate questions based on a knowledge graph."""
        graph_str = json.dumps(knowledge_graph, indent=2)
        prompt = f"""Generate {count} quiz questions for the topic: "{topic_name}".

Knowledge Graph:
{graph_str}

For each question, provide:
- question_text: The question
- correct_answer: The correct answer
- subtopic: Which subtopic this question relates to
- difficulty: easy, medium, or hard

Return a JSON array of questions:
[
    {{
        "question_text": "Question here?",
        "correct_answer": "Correct answer",
        "subtopic": "Subtopic name",
        "difficulty": "medium"
    }}
]

Only return the JSON array, no additional text."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a quiz question generator. Always return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
        )
        
        content = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        return json.loads(content)
    
    def grade_answer(self, question: str, correct_answer: str, user_answer: str) -> Tuple[bool, float, str]:
        """Grade a user's answer using LLM."""
        prompt = f"""You are grading a quiz answer. Evaluate the user's answer for correctness.

Question: {question}
Correct Answer: {correct_answer}
User's Answer: {user_answer}

Evaluate whether the user's answer is correct. Consider:
- Conceptual understanding (not just exact word matching)
- Partial correctness
- Common misconceptions

Return a JSON object with:
{{
    "is_correct": true/false,
    "confidence_score": 0.0-1.0,
    "feedback": "Brief explanation of why the answer is correct or incorrect, and what the correct answer should be"
}}

Only return the JSON object, no additional text."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an educational quiz grader. Always return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        
        content = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        result = json.loads(content)
        return (
            result.get('is_correct', False),
            result.get('confidence_score', 0.0),
            result.get('feedback', '')
        )


class AnthropicProvider(AIProvider):
    """Anthropic (Claude) provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Anthropic provider."""
        api_key = config.get('api_key')
        if not api_key:
            raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable.")
        self.client = Anthropic(api_key=api_key)
        self.model = config.get('model', 'claude-3-sonnet-20240229')
    
    def generate_knowledge_graph(self, topic_name: str) -> Dict[str, Any]:
        """Generate a knowledge graph structure for a topic."""
        prompt = f"""Generate a knowledge graph structure for the topic: "{topic_name}".

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

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system="You are a knowledge graph generator. Always return valid JSON only.",
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        
        content = response.content[0].text.strip()
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        return json.loads(content)
    
    def generate_questions(self, topic_name: str, knowledge_graph: Dict[str, Any], count: int = 10) -> List[Dict[str, Any]]:
        """Generate questions based on a knowledge graph."""
        graph_str = json.dumps(knowledge_graph, indent=2)
        prompt = f"""Generate {count} quiz questions for the topic: "{topic_name}".

Knowledge Graph:
{graph_str}

For each question, provide:
- question_text: The question
- correct_answer: The correct answer
- subtopic: Which subtopic this question relates to
- difficulty: easy, medium, or hard

Return a JSON array of questions:
[
    {{
        "question_text": "Question here?",
        "correct_answer": "Correct answer",
        "subtopic": "Subtopic name",
        "difficulty": "medium"
    }}
]

Only return the JSON array, no additional text."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system="You are a quiz question generator. Always return valid JSON only.",
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        
        content = response.content[0].text.strip()
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        return json.loads(content)
    
    def grade_answer(self, question: str, correct_answer: str, user_answer: str) -> Tuple[bool, float, str]:
        """Grade a user's answer using LLM."""
        prompt = f"""You are grading a quiz answer. Evaluate the user's answer for correctness.

Question: {question}
Correct Answer: {correct_answer}
User's Answer: {user_answer}

Evaluate whether the user's answer is correct. Consider:
- Conceptual understanding (not just exact word matching)
- Partial correctness
- Common misconceptions

Return a JSON object with:
{{
    "is_correct": true/false,
    "confidence_score": 0.0-1.0,
    "feedback": "Brief explanation of why the answer is correct or incorrect, and what the correct answer should be"
}}

Only return the JSON object, no additional text."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            system="You are an educational quiz grader. Always return valid JSON only.",
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        
        content = response.content[0].text.strip()
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        result = json.loads(content)
        return (
            result.get('is_correct', False),
            result.get('confidence_score', 0.0),
            result.get('feedback', '')
        )


class LocalProvider(AIProvider):
    """Local provider implementation (e.g., Ollama)."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize local provider."""
        from openai import OpenAI as LocalOpenAI
        
        base_url = config.get('base_url', 'http://localhost:11434/v1')
        if not base_url.endswith('/v1'):
            base_url = f"{base_url}/v1"
        
        self.client = LocalOpenAI(base_url=base_url, api_key='ollama')
        self.model = config.get('model', 'llama2')
    
    def generate_knowledge_graph(self, topic_name: str) -> Dict[str, Any]:
        """Generate a knowledge graph structure for a topic."""
        prompt = f"""Generate a knowledge graph structure for the topic: "{topic_name}".

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

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a knowledge graph generator. Always return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        content = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        return json.loads(content)
    
    def generate_questions(self, topic_name: str, knowledge_graph: Dict[str, Any], count: int = 10) -> List[Dict[str, Any]]:
        """Generate questions based on a knowledge graph."""
        graph_str = json.dumps(knowledge_graph, indent=2)
        prompt = f"""Generate {count} quiz questions for the topic: "{topic_name}".

Knowledge Graph:
{graph_str}

For each question, provide:
- question_text: The question
- correct_answer: The correct answer
- subtopic: Which subtopic this question relates to
- difficulty: easy, medium, or hard

Return a JSON array of questions:
[
    {{
        "question_text": "Question here?",
        "correct_answer": "Correct answer",
        "subtopic": "Subtopic name",
        "difficulty": "medium"
    }}
]

Only return the JSON array, no additional text."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a quiz question generator. Always return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
        )
        
        content = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        return json.loads(content)
    
    def grade_answer(self, question: str, correct_answer: str, user_answer: str) -> Tuple[bool, float, str]:
        """Grade a user's answer using LLM."""
        prompt = f"""You are grading a quiz answer. Evaluate the user's answer for correctness.

Question: {question}
Correct Answer: {correct_answer}
User's Answer: {user_answer}

Evaluate whether the user's answer is correct. Consider:
- Conceptual understanding (not just exact word matching)
- Partial correctness
- Common misconceptions

Return a JSON object with:
{{
    "is_correct": true/false,
    "confidence_score": 0.0-1.0,
    "feedback": "Brief explanation of why the answer is correct or incorrect, and what the correct answer should be"
}}

Only return the JSON object, no additional text."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an educational quiz grader. Always return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        
        content = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        result = json.loads(content)
        return (
            result.get('is_correct', False),
            result.get('confidence_score', 0.0),
            result.get('feedback', '')
        )


def get_ai_service() -> AIProvider:
    """Get the configured AI service provider."""
    config = get_config()
    provider_name = config.get_ai_provider()
    ai_config = config.get_ai_config()
    
    if provider_name == 'openai':
        return OpenAIProvider(ai_config)
    elif provider_name == 'anthropic':
        return AnthropicProvider(ai_config)
    elif provider_name == 'local':
        return LocalProvider(ai_config)
    else:
        raise ValueError(f"Unknown AI provider: {provider_name}")

