"""
Pydantic Models for API Request/Response and MongoDB Documents

These models define the structure for API endpoints and database storage.
"""

from datetime import datetime
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


# ============================================================================
# API Request Models
# ============================================================================

class GenerateMCQRequest(BaseModel):
    """Request model for MCQ generation (form fields)"""
    subject: str = Field(
        ...,
        description="Subject name (e.g., 'Calculus - Integration', 'Algebra', 'Physics')"
    )
    chapter: str = Field(
        ...,
        description="Chapter name (e.g., 'Chapter 3 - Definite Integrals', 'Introduction to Limits')"
    )
    input_type: Literal["chapter", "mcqs"] = Field(
        default="chapter",
        description="Type of input: 'chapter' content or existing 'mcqs'"
    )
    include_explanations: bool = Field(
        default=True,
        description="Include explanations in generated MCQs"
    )
    llm_provider: Optional[Literal["anthropic", "openai", "gemini"]] = Field(
        default=None,
        description="LLM provider (uses env default if not specified)"
    )
    model: Optional[str] = Field(
        default=None,
        description="Model name (uses env default if not specified)"
    )
    batch_size: Optional[int] = Field(
        default=None,
        description="Batch size for processing (uses env default if not specified)"
    )


# ============================================================================
# MongoDB Document Models
# ============================================================================

class ConceptDocument(BaseModel):
    """MongoDB document for extracted concepts"""
    concept_id: str
    concept_name: str
    formula: str
    difficulty: Literal["easy", "medium", "hard"]
    prerequisites: List[str]
    context: str
    worked_example: Optional[str] = None
    session_id: str
    subject: str
    chapter: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MCQDocument(BaseModel):
    """MongoDB document for complete MCQs"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    session_id: str
    user_id: Optional[str] = None
    subject: str
    chapter: str
    generation_query: Optional[str] = None
    question_number: int
    concept_id: str
    stem: str
    options: Dict[str, str]  # {"a": "...", "b": "...", "c": "...", "d": "..."}
    correct_answer: Literal["a", "b", "c", "d"]
    explanation: Dict[str, str]  # {"correct": "...", "a": "...", "b": "...", etc}
    answer_grading: Optional[Dict] = None
    metadata: Dict  # difficulty, validation scores, etc
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class MCQSessionDocument(BaseModel):
    """MongoDB document for generation sessions"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    session_id: str
    user_id: Optional[str] = None
    subject: str
    chapter: str
    generation_query: Optional[str] = None
    input_filename: str
    input_type: Literal["chapter", "mcqs"]
    llm_provider: str
    model: str
    batch_size: int
    total_concepts_extracted: int
    total_mcqs_generated: int
    difficulty_distribution: Dict[str, int]
    validation_rate: float
    metrics: Dict
    first_attempt_summary: Optional[Dict] = None
    status: Literal["processing", "completed", "failed"] = "processing"
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ============================================================================
# API Response Models
# ============================================================================

class MCQResponse(BaseModel):
    """Response model for individual MCQ"""
    id: str
    session_id: str
    subject: str
    chapter: str
    question_number: int
    concept_id: str
    stem: str
    options: Dict[str, str]
    correct_answer: str
    explanation: Dict[str, str]
    answer_grading: Optional[Dict] = None
    metadata: Dict
    created_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class SessionResponse(BaseModel):
    """Response model for generation session"""
    id: str
    session_id: str
    user_id: Optional[str] = None
    subject: str
    chapter: str
    generation_query: Optional[str] = None
    input_filename: str
    input_type: str
    llm_provider: str
    model: str
    total_concepts_extracted: int
    total_mcqs_generated: int
    difficulty_distribution: Dict[str, int]
    first_attempt_summary: Optional[Dict] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class GenerateMCQResponse(BaseModel):
    """Response model for MCQ generation endpoint"""
    session_id: str
    message: str
    total_mcqs_generated: int
    difficulty_distribution: Dict[str, int]
    metrics: Dict
    mcqs: List[MCQResponse]
    markdown_content: str
    learner_memory_enabled: Optional[bool] = None
    memory_hits: Optional[int] = None
    difficulty_hint_applied: Optional[str] = None
    topic_key: Optional[str] = None
    sub_topic_key: Optional[str] = None
    weak_focus_markdown: Optional[str] = None


class MCQListResponse(BaseModel):
    """Response model for listing MCQs"""
    total: int
    mcqs: List[MCQResponse]


class SessionListResponse(BaseModel):
    """Response model for listing sessions"""
    total: int
    sessions: List[SessionResponse]


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    database: str
    timestamp: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class FlashcardAttemptItem(BaseModel):
    """One flashcard interaction for a single MCQ."""

    mcq_id: Optional[str] = Field(None, description="api_mcq_id from generation response, e.g. sessionuuid_3")
    question_number: Optional[int] = Field(None, ge=1, description="Fallback if mcq_id not sent")
    selected: Optional[Literal["a", "b", "c", "d"]] = Field(None, description="Learner choice; omit if skipped")
    revealed_answer: bool = Field(False, description="Whether the learner revealed the correct answer")


class FlashcardFeedbackRequest(BaseModel):
    """Submit flashcard practice outcomes for Pinecone weak_concepts personalization."""

    session_id: str = Field(..., min_length=8)
    user_id: Optional[str] = Field(None, description="Body user id; can also use X-User-Id header")
    attempts: List[FlashcardAttemptItem] = Field(..., min_length=1)
    client_event_id: Optional[str] = Field(
        None,
        description="Idempotency key (e.g. UUID); duplicate submissions are ignored",
    )


class FlashcardFeedbackResponse(BaseModel):
    message: str
    weak_concepts_count: int = 0
    last_score: Optional[float] = None
    wrong_count: int = 0
    total_graded: int = 0
    pinecone_upserted: bool = False
    duplicate_event: bool = False
