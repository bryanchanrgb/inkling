"""FastAPI backend API for the Inkling learning application."""

import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from .models import Answer, Question, Topic
from .quiz_service import QuizService
from .storage import Storage
from .topic_service import TopicService

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("INFO:     Inkling API starting up...")
    yield
    print("INFO:     Inkling API shutting down...")

# Initialize FastAPI app
app = FastAPI(title="Inkling API", version="1.0.0", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
topic_service = TopicService()
quiz_service = QuizService()
storage = Storage()


# Pydantic models for request/response
class TopicCreate(BaseModel):
    name: str


class TopicResponse(BaseModel):
    id: Optional[int]
    name: str
    description: Optional[str]
    created_at: Optional[str]
    knowledge_graph_id: Optional[str]

    @classmethod
    def from_model(cls, topic: Topic):
        return cls(
            id=topic.id,
            name=topic.name,
            description=topic.description,
            created_at=topic.created_at.isoformat() if topic.created_at else None,
            knowledge_graph_id=topic.knowledge_graph_id,
        )


class SubtopicResponse(BaseModel):
    name: str
    description: Optional[str]


class QuestionResponse(BaseModel):
    id: Optional[int]
    topic_id: int
    question_text: str
    correct_answer: str
    subtopic: Optional[str]
    difficulty: Optional[str]

    @classmethod
    def from_model(cls, question: Question):
        return cls(
            id=question.id,
            topic_id=question.topic_id,
            question_text=question.question_text,
            correct_answer=question.correct_answer,
            subtopic=question.subtopic,
            difficulty=question.difficulty,
        )


class AnswerRequest(BaseModel):
    question_id: int
    user_answer: str


class AnswerResponse(BaseModel):
    id: Optional[int]
    question_id: int
    user_answer: str
    is_correct: bool
    understanding_score: Optional[int]
    feedback: Optional[str]
    timestamp: Optional[str]

    @classmethod
    def from_model(cls, answer: Answer):
        return cls(
            id=answer.id,
            question_id=answer.question_id,
            user_answer=answer.user_answer,
            is_correct=answer.is_correct,
            understanding_score=answer.understanding_score,
            feedback=answer.feedback,
            timestamp=answer.timestamp.isoformat() if answer.timestamp else None,
        )


class QuizResultsResponse(BaseModel):
    total_questions: int
    correct_answers: int
    incorrect_answers: int
    score: float
    average_understanding: float


class TopicCreateResponse(BaseModel):
    topic: TopicResponse
    questions: List[QuestionResponse]
    subtopics: List[SubtopicResponse]


class QuizHistoryEntry(BaseModel):
    id: int
    question_id: int
    question_text: str
    user_answer: str
    is_correct: bool
    understanding_score: Optional[int]
    feedback: Optional[str]
    timestamp: str
    topic_name: Optional[str]


# API Routes
@app.get("/")
async def root():
    return {"message": "Inkling API", "version": "1.0.0"}


@app.get("/api/topics", response_model=List[TopicResponse])
async def list_topics():
    """Get all topics."""
    try:
        topics = topic_service.list_topics()
        return [TopicResponse.from_model(topic) for topic in topics]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/topics/{topic_id}", response_model=TopicResponse)
async def get_topic(topic_id: int):
    """Get a topic by ID."""
    try:
        topic = topic_service.get_topic(topic_id)
        return TopicResponse.from_model(topic)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/topics", response_model=TopicCreateResponse, status_code=201)
async def create_topic(topic_data: TopicCreate):
    """Create a new topic with knowledge graph and questions."""
    try:
        if not topic_data.name.strip():
            raise HTTPException(status_code=400, detail="Topic name cannot be empty")

        # Check if topic already exists
        existing_topic = storage.get_topic_by_name(topic_data.name)
        if existing_topic:
            raise HTTPException(status_code=400, detail=f"Topic '{topic_data.name}' already exists")

        topic, questions = topic_service.create_topic(topic_data.name)
        subtopics = topic_service.get_subtopics(topic.name)

        return TopicCreateResponse(
            topic=TopicResponse.from_model(topic),
            questions=[QuestionResponse.from_model(q) for q in questions],
            subtopics=[SubtopicResponse(name=st["name"], description=st.get("description")) for st in subtopics],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/topics/{topic_id}/subtopics", response_model=List[SubtopicResponse])
async def get_subtopics(topic_id: int):
    """Get subtopics for a topic."""
    try:
        topic = topic_service.get_topic(topic_id)
        subtopics = topic_service.get_subtopics(topic.name)
        return [SubtopicResponse(name=st["name"], description=st.get("description")) for st in subtopics]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/quizzes/start", response_model=List[QuestionResponse])
async def start_quiz(topic_id: int, num_questions: Optional[int] = None):
    """Start a quiz for a topic."""
    try:
        questions = quiz_service.start_quiz(topic_id, num_questions)
        return [QuestionResponse.from_model(q) for q in questions]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/quizzes/grade", response_model=AnswerResponse)
async def grade_answer(answer_data: AnswerRequest):
    """Grade an answer to a question."""
    try:
        question = storage.get_question(answer_data.question_id)
        if not question:
            raise HTTPException(status_code=404, detail=f"Question {answer_data.question_id} not found")

        answer = quiz_service.grade_answer(question, answer_data.user_answer)
        return AnswerResponse.from_model(answer)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/quizzes/results", response_model=QuizResultsResponse)
async def get_quiz_results(answers: List[AnswerResponse]):
    """Calculate quiz results from a list of answers."""
    try:
        # Convert AnswerResponse back to Answer models
        answer_models = [
            Answer(
                id=a.id,
                question_id=a.question_id,
                user_answer=a.user_answer,
                is_correct=a.is_correct,
                understanding_score=a.understanding_score,
                feedback=a.feedback,
                timestamp=datetime.fromisoformat(a.timestamp) if a.timestamp else None,
            )
            for a in answers
        ]
        results = quiz_service.get_quiz_results(answer_models)
        return QuizResultsResponse(**results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/quizzes/history", response_model=List[QuizHistoryEntry])
async def get_quiz_history(topic_id: Optional[int] = None, limit: int = 20):
    """Get quiz history."""
    try:
        history = quiz_service.get_quiz_history(topic_id, limit)
        return [
            QuizHistoryEntry(
                id=record["id"],
                question_id=record["question_id"],
                question_text=record["question_text"],
                user_answer=record["user_answer"],
                is_correct=bool(record["is_correct"]),
                understanding_score=record.get("understanding_score"),
                feedback=record.get("feedback"),
                timestamp=record["timestamp"] if isinstance(record["timestamp"], str) else record["timestamp"].isoformat() if hasattr(record["timestamp"], "isoformat") else str(record["timestamp"]),
                topic_name=record.get("topic_name"),
            )
            for record in history
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/topics/{topic_id}/stats", response_model=List[Dict[str, Any]])
async def get_topic_stats(topic_id: int):
    """Get performance stats by subtopic for a topic."""
    try:
        return storage.get_subtopic_stats(topic_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/topics/{topic_id}/questions/generate", response_model=List[QuestionResponse])
async def generate_additional_questions(topic_id: int):
    """Generate additional questions for a topic."""
    try:
        question_data = quiz_service.generate_additional_questions(topic_id)

        if not question_data:
            return []

        # Save questions to database
        questions = []
        for q_data in question_data:
            question = Question(
                topic_id=topic_id,
                question_text=q_data.get("question_text", ""),
                correct_answer=q_data.get("correct_answer", ""),
                subtopic=q_data.get("subtopic"),
                difficulty=q_data.get("difficulty"),
            )
            question_id = storage.save_question(question)
            question.id = question_id
            questions.append(question)

        return [QuestionResponse.from_model(q) for q in questions]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/topics/{topic_id}/questions", response_model=List[QuestionResponse])
async def get_topic_questions(topic_id: int):
    """Get all questions for a topic."""
    try:
        questions = storage.get_questions_for_topic(topic_id)
        return [QuestionResponse.from_model(q) for q in questions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
