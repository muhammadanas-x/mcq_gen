"""
FastAPI Server for MCQ Generator

Provides REST API endpoints for generating MCQs and storing them in MongoDB Atlas.
Wraps the existing MCQGenerator without modifying its internal logic.
"""

import os
import uuid
import tempfile
import json
import re
import random
import asyncio
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from main import MCQGenerator
from database import get_async_database, close_async_database, ensure_mcq_indexes, COLLECTIONS
from models import (
    GenerateMCQResponse, MCQResponse, SessionResponse,
    MCQListResponse, SessionListResponse, HealthResponse,
    FlashcardFeedbackRequest, FlashcardFeedbackResponse,
)
from pymongo.errors import DuplicateKeyError
from answer_grading import build_answer_grading
from nodes.assembler import export_mcqs_to_markdown
import learner_memory

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="MCQ Generator API",
    description="Generate high-quality multiple-choice questions for calculus/integration topics",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Default configuration from environment
DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "openai")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "meta-llama/llama-3-8b-instruct")
DEFAULT_BATCH_SIZE = int(os.getenv("DEFAULT_BATCH_SIZE", "1"))
FALLBACK_LLM_PROVIDER = os.getenv("FALLBACK_LLM_PROVIDER", "openai")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "meta-llama/llama-3-8b-instruct")
FALLBACK_BATCH_SIZE = int(os.getenv("FALLBACK_BATCH_SIZE", "3"))

def _requested_mcq_count(query: Optional[str], default_count: int = 10) -> int:
    """
    Infer desired MCQ count from user query text.
    Examples: "give me 15 mcqs", "create 8 questions".
    """
    if not query:
        return default_count
    match = re.search(r"\b(\d{1,2})\s*(mcq|mcqs|questions?)\b", query.lower())
    if not match:
        return default_count
    count = int(match.group(1))
    return max(1, min(20, count))

def _parse_json_response(text: str):
    if "```json" in text:
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            text = match.group(1)
    elif "```" in text:
        match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            text = match.group(1)
    return json.loads(text, strict=False)

def _sync_prepend_learner_memory(
    path: str,
    subject: str,
    chapter: str,
    query: Optional[str],
    user_id: str,
    top_k: int = 8,
) -> dict:
    """Runs in thread: query Pinecone and prepend weak-focus + memory block to chapter markdown."""
    td, sd, tk, sk = learner_memory.topic_subtopic_from_strings(subject, chapter)
    qt = (query or "").strip() or f"{td} {sd}"
    bundle = learner_memory.query_memory_bundle(user_id, tk, sk, qt, top_k=top_k)
    composed = learner_memory.compose_learner_prefix_for_generation(bundle)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if composed.strip() and (
        int(bundle.get("memory_hits") or 0) > 0 or (bundle.get("weak_focus_markdown") or "").strip()
    ):
        with open(path, "w", encoding="utf-8") as f:
            f.write(composed.strip() + "\n\n" + content)
    return {
        "memory_hits": bundle["memory_hits"],
        "difficulty_hint": bundle["difficulty_hint"],
        "topic_key": tk,
        "sub_topic_key": sk,
        "learner_context": bundle.get("learner_context") or "",
        "weak_focus_markdown": bundle.get("weak_focus_markdown") or "",
    }


async def _prepend_learner_memory_file(
    path: Optional[str],
    subject: str,
    chapter: str,
    query: Optional[str],
    user_id: Optional[str],
    top_k: int = 8,
) -> dict:
    if not path or not user_id or not learner_memory.is_configured():
        td, sd, tk, sk = learner_memory.topic_subtopic_from_strings(subject, chapter)
        return {
            "memory_hits": 0,
            "difficulty_hint": "medium",
            "topic_key": tk,
            "sub_topic_key": sk,
            "learner_context": "",
            "weak_focus_markdown": "",
        }
    return await asyncio.to_thread(_sync_prepend_learner_memory, path, subject, chapter, query, user_id, top_k)


def _normalize_openrouter_mcqs_payload(
    raw_mcqs: list,
    *,
    include_explanations: bool,
    max_items: int,
) -> List[dict]:
    """Turn model JSON `mcqs` array into the internal dict shape used by `/generate-mcqs`."""
    cap = max(1, min(20, int(max_items or 10)))
    normalized: List[dict] = []
    if not isinstance(raw_mcqs, list):
        return []
    for item in raw_mcqs:
        if len(normalized) >= cap:
            break
        if not isinstance(item, dict):
            continue
        options = item.get("options", {})
        if not isinstance(options, dict) or not all(k in options for k in ["a", "b", "c", "d"]):
            continue
        answer = str(item.get("correct_answer", "")).lower().strip()
        if answer not in ["a", "b", "c", "d"]:
            continue

        explanation = {"correct": item.get("correct_explanation", "Correct option by standard method.")}
        if include_explanations:
            for key in ["a", "b", "c", "d"]:
                explanation[key] = "Option analysis available in tutor mode."

        normalized.append(
            {
                "question_number": len(normalized) + 1,
                "concept_id": str(item.get("concept_id", f"query_concept_{len(normalized) + 1}")),
                "stem": str(item.get("stem", f"Generated question {len(normalized) + 1}")),
                "options": options,
                "correct_answer": answer,
                "explanation": explanation,
                "metadata": {
                    "difficulty": str(item.get("difficulty", "medium")),
                    "validation_score": 1.0,
                    "was_corrected": False,
                    "integral_type": "query_generated",
                },
            }
        )
    return normalized


def _openrouter_flashcards_single_call(
    *,
    subject: str,
    chapter: str,
    query: str,
    desired_count: int,
    model: str,
    include_explanations: bool,
    learner_context: str = "",
    difficulty_hint: str = "medium",
) -> List[dict]:
    """
    One OpenRouter-compatible ChatOpenAI completion → MCQ list (Hub / flash cards).
    No LangGraph.
    """
    n = max(1, min(20, int(desired_count)))
    llm = ChatOpenAI(
        model=model,
        temperature=0.35,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
    )

    system_prompt = (
        "You are an expert mathematics MCQ generator. "
        "Return ONLY valid JSON with this shape:\n"
        "{\n"
        '  "mcqs": [\n'
        "    {\n"
        '      "stem": "question text",\n'
        '      "options": {"a":"...", "b":"...", "c":"...", "d":"..."},\n'
        '      "correct_answer": "a|b|c|d",\n'
        '      "difficulty": "easy|medium|hard",\n'
        '      "concept_id": "short_id",\n'
        '      "correct_explanation": "why answer is correct"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        f"Generate **exactly {n}** MCQs. Each must have exactly four options a–d and a valid correct_answer."
    )

    user_prompt = (
        f"Subject: {subject}\n"
        f"Chapter: {chapter}\n"
        f"User query/topic: {query}\n"
        "Generate conceptual and calculation-based MCQs aligned with the chapter."
    )
    if (learner_context or "").strip():
        user_prompt += (
            f"\n\nPrior learner activity (do not repeat verbatim stems):\n{learner_context[:4000]}\n"
            f"\nTarget difficulty bias for NEW items: **{difficulty_hint}**."
        )

    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
    )
    data = _parse_json_response(response.content)
    raw_mcqs = data.get("mcqs", [])
    if not isinstance(raw_mcqs, list):
        return []
    return _normalize_openrouter_mcqs_payload(
        raw_mcqs,
        include_explanations=include_explanations,
        max_items=n,
    )


def _generate_mcqs_from_query_direct(
    subject: str,
    chapter: str,
    query: str,
    model: str,
    include_explanations: bool,
    learner_context: str = "",
    difficulty_hint: str = "medium",
):
    """
    Direct query-to-MCQ fallback when the full pipeline returns zero questions.
    """
    return _openrouter_flashcards_single_call(
        subject=subject,
        chapter=chapter,
        query=query,
        desired_count=10,
        model=model,
        include_explanations=include_explanations,
        learner_context=learner_context,
        difficulty_hint=difficulty_hint,
    )

def _generate_mock_mcqs(
    subject: str,
    chapter: str,
    requested_count: int = 10,
    include_explanations: bool = True
):
    """
    Guaranteed fallback set so frontend can always render flash cards.
    """
    topic = f"{subject} - {chapter}".strip(" -")
    templates = [
        ("What is the derivative of $x^2$?", {"a": "$2x$", "b": "$x$", "c": "$x^2$", "d": "$2$"}, "a"),
        ("Evaluate $\\int 2x\\,dx$.", {"a": "$x^2 + C$", "b": "$2x + C$", "c": "$x + C$", "d": "$2x^2 + C$"}, "a"),
        ("$\\sin^2 x + \\cos^2 x =$ ?", {"a": "$1$", "b": "$0$", "c": "$\\sin x$", "d": "$\\cos x$"}, "a"),
        ("Derivative of $\\ln x$ is:", {"a": "$1/x$", "b": "$x$", "c": "$\\ln x$", "d": "$e^x$"}, "a"),
        ("$\\int \\frac{1}{x}\\,dx =$", {"a": "$\\ln|x| + C$", "b": "$1/x + C$", "c": "$x + C$", "d": "$e^x + C$"}, "a"),
        ("$\\frac{d}{dx}(e^x) =$", {"a": "$e^x$", "b": "$xe^{x-1}$", "c": "$x^e$", "d": "$1$"}, "a"),
        ("For $f(x)=x^3$, $f'(x)=$", {"a": "$3x^2$", "b": "$x^2$", "c": "$3x$", "d": "$x^3$"}, "a"),
        ("$\\int \\cos x\\,dx =$", {"a": "$\\sin x + C$", "b": "$-\\sin x + C$", "c": "$\\cos x + C$", "d": "$-\\cos x + C$"}, "a"),
        ("$\\int \\sin x\\,dx =$", {"a": "$-\\cos x + C$", "b": "$\\cos x + C$", "c": "$\\sin x + C$", "d": "$-\\sin x + C$"}, "a"),
        ("Power rule: $\\int x^n\\,dx =$", {"a": "$\\frac{x^{n+1}}{n+1}+C$", "b": "$nx^{n-1}+C$", "c": "$x^{n-1}+C$", "d": "$\\frac{x^n}{n}+C$"}, "a"),
    ]
    generated = []
    for idx in range(1, requested_count + 1):
        stem, options, correct = random.choice(templates)
        explanation = {
            "correct": f"Mock fallback card for {topic}. Replace with model output when credits are available."
        }
        if include_explanations:
            for key in ["a", "b", "c", "d"]:
                explanation[key] = "Fallback explanation."
        generated.append({
            "question_number": idx,
            "concept_id": f"mock_{idx}",
            "stem": f"[Mock] {stem}",
            "options": options,
            "correct_answer": correct,
            "explanation": explanation,
            "metadata": {
                "difficulty": random.choice(["easy", "medium", "hard"]),
                "validation_score": 1.0,
                "was_corrected": False,
                "integral_type": "mock_fallback",
            },
        })
    return generated


def _build_first_attempt_summary(mcqs: List[dict]) -> dict:
    total_questions = len(mcqs)
    total_correct = 0
    total_wrong = 0
    for mcq in mcqs:
        grading = mcq.get("answer_grading") or {}
        total_correct += len(grading.get("correct_keys") or [])
        total_wrong += len(grading.get("incorrect_keys") or [])

    return {
        "total_questions": total_questions,
        "total_correct": total_correct,
        "total_wrong": total_wrong,
        "captured_at": datetime.utcnow(),
        "source": "first_generation_attempt",
    }


@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    await get_async_database()
    await ensure_mcq_indexes()
    print("[OK] FastAPI server started")
    print("[OK] MongoDB connection initialized")
    print("[OK] MongoDB indexes ensured")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await close_async_database()
    print("[OK] MongoDB connection closed")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "MCQ Generator API",
        "version": "1.0.0",
        "endpoints": {
            "generate": "POST /generate-mcqs",
            "list_sessions": "GET /sessions",
            "get_session": "GET /sessions/{session_id}",
            "list_mcqs": "GET /mcqs",
            "get_mcq": "GET /mcqs/{mcq_id}",
            "health": "GET /health",
            "flashcard_feedback": "POST /flashcard-feedback",
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Verifies API and database connectivity.
    """
    try:
        db = await get_async_database()
        # Test database connection
        await db.command("ping")
        
        return HealthResponse(
            status="healthy",
            database="connected",
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")


@app.post("/generate-mcqs", response_model=GenerateMCQResponse, tags=["Generation"])
async def generate_mcqs(
    file: UploadFile = File(None, description="Optional input file (chapter.md or existing MCQs)"),
    subject: str = Form(..., description="Subject name (e.g., 'Calculus', 'Linear Algebra')"),
    chapter: str = Form(..., description="Chapter name (e.g., 'Chapter 3 - Definite Integrals')"),
    topic: Optional[str] = Form(None, description="Optional display topic; when set, overrides subject for storage/memory"),
    sub_topic: Optional[str] = Form(None, description="Optional display sub-topic; when set, overrides chapter for storage/memory"),
    query: Optional[str] = Form(None, description="Optional natural-language query/topic for on-the-fly generation"),
    input_type: str = Form("chapter", description="Type of input: 'chapter' or 'mcqs'"),
    include_explanations: bool = Form(True, description="Include explanations in MCQs"),
    user_id: Optional[str] = Form(None, description="Logged-in user id"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id")
):
    """
    Generate MCQs from uploaded file.
    
    This endpoint accepts a markdown file (chapter content or existing MCQs)
    and generates new MCQs using the LLM configuration from environment variables.
    
    The generation is synchronous - the endpoint returns after completion.
    All results are stored in MongoDB Atlas organized by subject and chapter.
    
    Configuration is read from .env file:
    - DEFAULT_LLM_PROVIDER (gemini/openai/anthropic)
    - DEFAULT_MODEL (model name)
    - DEFAULT_BATCH_SIZE (batch size)
    """
    
    # Validate source and mode
    if not file and not (query and query.strip()):
        raise HTTPException(status_code=400, detail="Provide either an uploaded markdown file or a query")
    if input_type not in ["chapter", "mcqs"]:
        raise HTTPException(status_code=400, detail="input_type must be 'chapter' or 'mcqs'")

    effective_subject = ((topic or "").strip() or (subject or "").strip())
    effective_chapter = ((sub_topic or "").strip() or (chapter or "").strip())
    if not effective_subject or not effective_chapter:
        raise HTTPException(status_code=400, detail="subject/topic and chapter/sub_topic are required")
    
    # Use configuration from environment variables
    llm_provider = DEFAULT_LLM_PROVIDER
    model = DEFAULT_MODEL
    batch_size = DEFAULT_BATCH_SIZE
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    resolved_user_id = (user_id or x_user_id or "").strip() or None
    desired_count = _requested_mcq_count(query, default_count=10)
    mem_stats: dict = {
        "memory_hits": 0,
        "difficulty_hint": "medium",
        "topic_key": "",
        "sub_topic_key": "",
        "learner_context": "",
        "weak_focus_markdown": "",
    }
    # Hub flash cards: query-only, no uploaded file (same as frontend generateMCQsFromQuery).
    hub_query_mode = bool(file is None and query and query.strip())

    # Create temporary file to store uploaded content
    temp_file_path = None

    try:
        # Save uploaded file OR synthesize temporary markdown from query
        if file:
            if not file.filename.endswith('.md'):
                raise HTTPException(status_code=400, detail="File must be a markdown (.md) file")
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.md') as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
        else:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md', encoding='utf-8') as temp_file:
                temp_file.write(f"# {effective_subject}\n\n## {effective_chapter}\n\n{query.strip()}\n")
                temp_file_path = temp_file.name
            input_type = "chapter"

        # For Hub flashcard generation, retrieve a wider memory set and let
        # learner_memory apply similarity threshold filtering.
        rag_top_k = 20 if hub_query_mode else 8
        _mem = await _prepend_learner_memory_file(
            temp_file_path,
            effective_subject,
            effective_chapter,
            query,
            resolved_user_id,
            top_k=rag_top_k,
        )
        mem_stats.update(_mem)

        print(f"\n{'='*60}")
        print(f"API REQUEST - Session ID: {session_id}")
        print(f"{'='*60}")
        print(f"Subject: {effective_subject}")
        print(f"Chapter: {effective_chapter}")
        print(f"Source: {file.filename if file else 'query'}")
        print(f"Input Type: {input_type}")
        print(f"Hub query-only (skip LangGraph): {hub_query_mode}")
        print(f"LLM: {llm_provider} - {model}")
        print(f"Batch Size: {batch_size}")
        print(f"{'='*60}\n")

        mcqs: List[dict] = []
        if hub_query_mode:
            # Single OpenRouter-style completion path (no MCQGenerator / LangGraph).
            llm_provider = DEFAULT_LLM_PROVIDER
            batch_size = 1
            learner_prefix = learner_memory.compose_learner_prefix_for_generation(mem_stats).strip()[:12000]
            difficulty_hint = mem_stats.get("difficulty_hint") or "medium"
            last_err: Optional[Exception] = None
            for attempt_model in (DEFAULT_MODEL, FALLBACK_MODEL):
                try:
                    mcqs = await asyncio.to_thread(
                        _openrouter_flashcards_single_call,
                        subject=effective_subject,
                        chapter=effective_chapter,
                        query=query.strip(),
                        desired_count=desired_count,
                        model=attempt_model,
                        include_explanations=include_explanations,
                        learner_context=learner_prefix,
                        difficulty_hint=difficulty_hint,
                    )
                    if mcqs:
                        model = attempt_model
                        break
                except Exception as ex:
                    last_err = ex
                    print(f"\n[Hub flashcards] OpenRouter call failed for model={attempt_model}: {ex}\n")
            if not mcqs:
                detail = (
                    "Hub flashcard generation produced no valid MCQs from the model response."
                    + (f" Last error: {last_err}" if last_err else "")
                )
                raise HTTPException(status_code=502, detail=detail)
        else:
            # Initialize MCQ Generator with specified configuration
            generator = MCQGenerator(
                llm_provider=llm_provider,
                model=model,
                batch_size=batch_size
            )

            # Generate MCQs (synchronous - waits for completion)
            # If provider fails (timeout, rate-limit, etc.), keep flowing to fallback cards.
            try:
                mcqs = generator.generate_from_file(
                    input_path=temp_file_path,
                    input_type=input_type,
                    output_path=None,  # We'll handle export separately
                    include_explanations=include_explanations
                )
            except Exception as primary_error:
                err_text = str(primary_error)
                print("\n" + "="*60)
                print("Primary provider request failed; attempting fallback provider")
                print(f"Primary error: {err_text}")
                print(f"Fallback LLM: {FALLBACK_LLM_PROVIDER} - {FALLBACK_MODEL}")
                print(f"Fallback batch size: {FALLBACK_BATCH_SIZE}")
                print("="*60 + "\n")

                llm_provider = FALLBACK_LLM_PROVIDER
                model = FALLBACK_MODEL
                batch_size = FALLBACK_BATCH_SIZE

                try:
                    fallback_generator = MCQGenerator(
                        llm_provider=llm_provider,
                        model=model,
                        batch_size=batch_size
                    )
                    mcqs = fallback_generator.generate_from_file(
                        input_path=temp_file_path,
                        input_type=input_type,
                        output_path=None,
                        include_explanations=include_explanations
                    )
                except Exception as fallback_error:
                    print(f"Fallback provider failed: {fallback_error}")
                    mcqs = []

            # Last-mile fallback: if pipeline produced no cards, generate directly from query.
            if len(mcqs) == 0 and query and query.strip():
                print("\n" + "="*60)
                print("Pipeline returned 0 MCQs; using direct query-based generation fallback")
                print("="*60 + "\n")
                try:
                    mcqs = _generate_mcqs_from_query_direct(
                        subject=effective_subject,
                        chapter=effective_chapter,
                        query=query.strip(),
                        model=FALLBACK_MODEL,
                        include_explanations=include_explanations,
                        learner_context=learner_memory.compose_learner_prefix_for_generation(mem_stats).strip()[:12000],
                        difficulty_hint=mem_stats.get("difficulty_hint") or "medium",
                    )
                except Exception as direct_error:
                    print(f"Direct generation fallback failed: {direct_error}")
                    mcqs = []

            # Hard guarantee fallback for UI testing (not used for Hub query-only mode):
            # if still empty OR less than requested, pad using deterministic mock cards.
            if len(mcqs) == 0:
                print("\nUsing mock MCQ fallback (no model output available).")
                mcqs = _generate_mock_mcqs(
                    subject=effective_subject,
                    chapter=effective_chapter,
                    requested_count=desired_count,
                    include_explanations=include_explanations,
                )
            elif len(mcqs) < desired_count:
                print(f"\nTop-up fallback: generated {len(mcqs)}, requested {desired_count}.")
                extras = _generate_mock_mcqs(
                    subject=effective_subject,
                    chapter=effective_chapter,
                    requested_count=desired_count - len(mcqs),
                    include_explanations=include_explanations,
                )
                # Continue numbering and append mock extras
                start_idx = len(mcqs) + 1
                for i, extra in enumerate(extras, start=start_idx):
                    extra["question_number"] = i
                    extra["concept_id"] = f"mock_{i}"
                mcqs.extend(extras)
        
        # Deterministic grading payload for each option set
        for mcq in mcqs:
            mcq["answer_grading"] = build_answer_grading(mcq)

        # Calculate metrics
        difficulty_dist = {}
        for mcq in mcqs:
            diff = mcq['metadata']['difficulty']
            difficulty_dist[diff] = difficulty_dist.get(diff, 0) + 1
        
        metrics = {
            "total_concepts_extracted": len(mcqs),
            "total_mcqs_generated": len(mcqs),
            "validation_rate": 1.0,  # Since validator is pass-through
            "difficulty_distribution": difficulty_dist
        }
        
        # Generate markdown content
        markdown_output = []
        markdown_output.append(f"### Generated MCQs: Integration")
        markdown_output.append(f"#### PRACTICE EXERCISE")
        markdown_output.append(f"")
        
        from nodes.assembler import format_mcq_markdown
        for mcq in mcqs:
            mcq_text = format_mcq_markdown(mcq, include_explanations)
            markdown_output.append(mcq_text)
        
        markdown_content = "\n".join(markdown_output)
        
        # Persist session + MCQs in MongoDB.
        db = await get_async_database()
        now = datetime.utcnow()
        generation_query = query.strip() if query and query.strip() else None
        session_doc = {
            "session_id": session_id,
            "user_id": resolved_user_id,
            "subject": effective_subject,
            "chapter": effective_chapter,
            "generation_query": generation_query,
            "input_filename": file.filename if file else "query_input.md",
            "input_type": input_type,
            "llm_provider": llm_provider,
            "model": model,
            "batch_size": batch_size,
            "total_concepts_extracted": len(mcqs),
            "total_mcqs_generated": len(mcqs),
            "difficulty_distribution": difficulty_dist,
            "validation_rate": metrics.get("validation_rate", 1.0),
            "metrics": metrics,
            "first_attempt_summary": _build_first_attempt_summary(mcqs),
            "status": "completed",
            "error_message": None,
            "created_at": now,
            "completed_at": now,
        }
        await db[COLLECTIONS["mcq_sessions"]].update_one(
            {"session_id": session_id},
            {"$setOnInsert": session_doc},
            upsert=True,
        )

        mcq_docs = []
        mcq_responses = []
        for i, mcq in enumerate(mcqs, start=1):
            api_mcq_id = f"{session_id}_{i}"
            mcq_docs.append({
                "api_mcq_id": api_mcq_id,
                "session_id": session_id,
                "user_id": resolved_user_id,
                "subject": effective_subject,
                "chapter": effective_chapter,
                "generation_query": generation_query,
                "question_number": mcq.get("question_number", i),
                "concept_id": mcq.get("concept_id", f"concept_{i}"),
                "stem": mcq["stem"],
                "options": mcq["options"],
                "correct_answer": mcq["correct_answer"],
                "explanation": mcq["explanation"],
                "answer_grading": mcq.get("answer_grading"),
                "metadata": mcq["metadata"],
                "created_at": now,
            })
            mcq_responses.append(MCQResponse(
                id=api_mcq_id,
                session_id=session_id,
                subject=effective_subject,
                chapter=effective_chapter,
                question_number=mcq.get("question_number", i),
                concept_id=mcq.get("concept_id", f"concept_{i}"),
                stem=mcq["stem"],
                options=mcq["options"],
                correct_answer=mcq["correct_answer"],
                explanation=mcq["explanation"],
                answer_grading=mcq.get("answer_grading"),
                metadata=mcq["metadata"],
                created_at=now
            ))
        if mcq_docs:
            await db[COLLECTIONS["mcqs"]].insert_many(mcq_docs, ordered=True)

        memory_enabled = bool(resolved_user_id and learner_memory.is_configured())

        print(f"\n{'='*60}")
        print(f"[OK] Generation completed successfully!")
        print(f"[OK] Session ID: {session_id}")
        print(f"[OK] MCQs generated: {len(mcqs)}")
        print(f"[OK] Session and MCQs saved to MongoDB")
        print(f"{'='*60}\n")
        
        return GenerateMCQResponse(
            session_id=session_id,
            message="MCQs generated successfully",
            total_mcqs_generated=len(mcqs),
            difficulty_distribution=difficulty_dist,
            metrics=metrics,
            mcqs=mcq_responses,
            markdown_content=markdown_content,
            learner_memory_enabled=memory_enabled,
            memory_hits=int(mem_stats.get("memory_hits") or 0),
            difficulty_hint_applied=str(mem_stats.get("difficulty_hint") or "medium"),
            topic_key=(mem_stats.get("topic_key") or "") or None,
            sub_topic_key=(mem_stats.get("sub_topic_key") or "") or None,
            weak_focus_markdown=(mem_stats.get("weak_focus_markdown") or "").strip() or None,
        )

    except HTTPException:
        raise
    except Exception as e:
        # Safety net for provider paths that still raise "no questions" upstream.
        # We degrade to deterministic mock cards instead of failing the API call.
        err_text = str(e)
        if hub_query_mode:
            print(f"\n{'='*60}")
            print(f"[ERR] Hub query-only generation failed!")
            print(f"[ERR] Session ID: {session_id}")
            print(f"[ERR] Error: {str(e)}")
            print(f"{'='*60}\n")
            raise HTTPException(status_code=500, detail=f"MCQ generation failed: {str(e)}")
        lowered = err_text.lower()
        if "produced no questions" in lowered or "mock fallback is disabled" in lowered:
            try:
                emergency_mcqs = _generate_mock_mcqs(
                    subject=effective_subject,
                    chapter=effective_chapter,
                    requested_count=desired_count,
                    include_explanations=include_explanations,
                )
                for mcq in emergency_mcqs:
                    mcq["answer_grading"] = build_answer_grading(mcq)

                emergency_dist = {}
                for mcq in emergency_mcqs:
                    diff = mcq["metadata"]["difficulty"]
                    emergency_dist[diff] = emergency_dist.get(diff, 0) + 1

                emergency_metrics = {
                    "total_concepts_extracted": len(emergency_mcqs),
                    "total_mcqs_generated": len(emergency_mcqs),
                    "validation_rate": 1.0,
                    "difficulty_distribution": emergency_dist,
                }

                markdown_output = [
                    "### Generated MCQs: Integration",
                    "#### PRACTICE EXERCISE",
                    "",
                ]
                from nodes.assembler import format_mcq_markdown
                for mcq in emergency_mcqs:
                    markdown_output.append(format_mcq_markdown(mcq, include_explanations))
                markdown_content = "\n".join(markdown_output)

                db = await get_async_database()
                now = datetime.utcnow()
                generation_query = query.strip() if query and query.strip() else None
                session_doc = {
                    "session_id": session_id,
                    "user_id": resolved_user_id,
                    "subject": effective_subject,
                    "chapter": effective_chapter,
                    "generation_query": generation_query,
                    "input_filename": file.filename if file else "query_input.md",
                    "input_type": input_type,
                    "llm_provider": llm_provider,
                    "model": model,
                    "batch_size": batch_size,
                    "total_concepts_extracted": len(emergency_mcqs),
                    "total_mcqs_generated": len(emergency_mcqs),
                    "difficulty_distribution": emergency_dist,
                    "validation_rate": emergency_metrics.get("validation_rate", 1.0),
                    "metrics": emergency_metrics,
                    "first_attempt_summary": _build_first_attempt_summary(emergency_mcqs),
                    "status": "completed_with_mock_fallback",
                    "error_message": err_text[:1200],
                    "created_at": now,
                    "completed_at": now,
                }
                await db[COLLECTIONS["mcq_sessions"]].update_one(
                    {"session_id": session_id},
                    {"$setOnInsert": session_doc},
                    upsert=True,
                )

                mcq_docs = []
                mcq_responses = []
                for i, mcq in enumerate(emergency_mcqs, start=1):
                    api_mcq_id = f"{session_id}_{i}"
                    mcq_docs.append({
                        "api_mcq_id": api_mcq_id,
                        "session_id": session_id,
                        "user_id": resolved_user_id,
                        "subject": effective_subject,
                        "chapter": effective_chapter,
                        "generation_query": generation_query,
                        "question_number": mcq.get("question_number", i),
                        "concept_id": mcq.get("concept_id", f"concept_{i}"),
                        "stem": mcq["stem"],
                        "options": mcq["options"],
                        "correct_answer": mcq["correct_answer"],
                        "explanation": mcq["explanation"],
                        "answer_grading": mcq.get("answer_grading"),
                        "metadata": mcq["metadata"],
                        "created_at": now,
                    })
                    mcq_responses.append(MCQResponse(
                        id=api_mcq_id,
                        session_id=session_id,
                        subject=effective_subject,
                        chapter=effective_chapter,
                        question_number=mcq.get("question_number", i),
                        concept_id=mcq.get("concept_id", f"concept_{i}"),
                        stem=mcq["stem"],
                        options=mcq["options"],
                        correct_answer=mcq["correct_answer"],
                        explanation=mcq["explanation"],
                        answer_grading=mcq.get("answer_grading"),
                        metadata=mcq["metadata"],
                        created_at=now,
                    ))
                if mcq_docs:
                    await db[COLLECTIONS["mcqs"]].insert_many(mcq_docs, ordered=True)

                memory_enabled = bool(resolved_user_id and learner_memory.is_configured())
                return GenerateMCQResponse(
                    session_id=session_id,
                    message="MCQs generated using mock fallback (provider returned no questions)",
                    total_mcqs_generated=len(emergency_mcqs),
                    difficulty_distribution=emergency_dist,
                    metrics=emergency_metrics,
                    mcqs=mcq_responses,
                    markdown_content=markdown_content,
                    learner_memory_enabled=memory_enabled,
                    memory_hits=int(mem_stats.get("memory_hits") or 0),
                    difficulty_hint_applied=str(mem_stats.get("difficulty_hint") or "medium"),
                    topic_key=(mem_stats.get("topic_key") or "") or None,
                    sub_topic_key=(mem_stats.get("sub_topic_key") or "") or None,
                    weak_focus_markdown=(mem_stats.get("weak_focus_markdown") or "").strip() or None,
                )
            except Exception as fallback_error:
                print(f"[ERR] Emergency mock fallback failed: {fallback_error}")

        print(f"\n{'='*60}")
        print(f"[ERR] Generation failed!")
        print(f"[ERR] Session ID: {session_id}")
        print(f"[ERR] Error: {str(e)}")
        print(f"{'='*60}\n")
        
        raise HTTPException(status_code=500, detail=f"MCQ generation failed: {str(e)}")
    
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


@app.post("/flashcard-feedback", response_model=FlashcardFeedbackResponse, tags=["Learner memory"])
async def flashcard_feedback(
    payload: FlashcardFeedbackRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """
    Record flashcard practice outcomes and upsert a Pinecone vector with weak_concepts
    for later RAG during MCQ generation.
    """
    uid = (payload.user_id or x_user_id or "").strip()
    if not uid:
        raise HTTPException(status_code=400, detail="user_id is required (form field or X-User-Id header)")

    db = await get_async_database()

    sess = await db[COLLECTIONS["mcq_sessions"]].find_one({"session_id": payload.session_id})
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    mcqs = (
        await db[COLLECTIONS["mcqs"]]
        .find({"session_id": payload.session_id})
        .sort("question_number", 1)
        .to_list(length=500)
    )
    if not mcqs:
        raise HTTPException(status_code=400, detail="No MCQs found for this session")

    su = (sess.get("user_id") or "").strip()
    if su and su != uid:
        raise HTTPException(status_code=403, detail="Session does not belong to this user")
    if not su:
        mu = (mcqs[0].get("user_id") or "").strip()
        if mu and mu != uid:
            raise HTTPException(status_code=403, detail="MCQs in this session belong to a different user")

    by_id = {m["api_mcq_id"]: m for m in mcqs if m.get("api_mcq_id")}
    by_num = {int(m["question_number"]): m for m in mcqs if m.get("question_number") is not None}

    weak: List[str] = []
    wrong = 0
    correct = 0
    graded = 0

    for att in payload.attempts:
        m = None
        if att.mcq_id and att.mcq_id in by_id:
            m = by_id[att.mcq_id]
        elif att.question_number is not None and att.question_number in by_num:
            m = by_num[att.question_number]
        if not m:
            continue
        if not att.selected:
            continue
        graded += 1
        ca = str(m.get("correct_answer", "")).strip().lower()
        sel = att.selected.lower()
        if sel == ca:
            correct += 1
            continue
        wrong += 1
        stem_snip = re.sub(r"\s+", " ", (m.get("stem") or ""))[:120]
        concept_id_s = str(m.get("concept_id", ""))
        qn = m.get("question_number", "?")
        weak.append(f"Q{qn}: chose ({sel}) vs correct ({ca}); concept={concept_id_s}; stem: {stem_snip}")

    if graded == 0:
        raise HTTPException(
            status_code=400,
            detail="No graded attempts: include selected option for each attempted card",
        )

    weak = weak[:20]
    last_score = round(100.0 * correct / graded, 1)

    cid = (payload.client_event_id or "").strip()
    if cid:
        existing = await db[COLLECTIONS["flashcard_feedback_dedup"]].find_one(
            {"user_id": uid, "client_event_id": cid}
        )
        if existing:
            return FlashcardFeedbackResponse(
                message="Duplicate client_event_id; ignored.",
                weak_concepts_count=0,
                last_score=None,
                wrong_count=0,
                total_graded=0,
                pinecone_upserted=False,
                duplicate_event=True,
            )

    pinecone_ok = False
    if learner_memory.is_configured() and weak:
        excerpt_mem = weak[0][:800]
        prompt_mem = (sess.get("generation_query") or "").strip() or "flashcard_practice"
        vid = await asyncio.to_thread(
            learner_memory.upsert_memory_record,
            user_id=uid,
            topic=str(sess.get("subject") or ""),
            sub_topic=str(sess.get("chapter") or ""),
            prompt=prompt_mem,
            source="mcq_flashcard_practice",
            session_id=payload.session_id,
            excerpt=excerpt_mem,
            weak_concepts=weak,
            last_score=last_score,
            wrong_count=wrong,
            total_attempted=graded,
        )
        pinecone_ok = bool(vid)
        if pinecone_ok and cid:
            try:
                await db[COLLECTIONS["flashcard_feedback_dedup"]].insert_one(
                    {"user_id": uid, "client_event_id": cid, "created_at": datetime.utcnow()}
                )
            except DuplicateKeyError:
                pass

    return FlashcardFeedbackResponse(
        message="Flashcard feedback recorded",
        weak_concepts_count=len(weak),
        last_score=last_score,
        wrong_count=wrong,
        total_graded=graded,
        pinecone_upserted=pinecone_ok,
        duplicate_event=False,
    )


@app.get("/sessions", response_model=SessionListResponse, tags=["Sessions"])
async def list_sessions(
    subject: Optional[str] = Query(None, description="Filter by subject"),
    chapter: Optional[str] = Query(None, description="Filter by chapter"),
    session_id: Optional[str] = Query(None, description="Filter by exact session_id (deep link)"),
    skip: int = Query(0, ge=0, description="Number of sessions to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum sessions to return")
):
    """
    List all MCQ generation sessions.
    
    Optionally filter by subject, chapter, and/or session_id. Returns paginated list of sessions with metadata.
    """
    db = await get_async_database()
    
    # Build query filter
    query_filter = {}
    if subject:
        query_filter["subject"] = subject
    if chapter:
        query_filter["chapter"] = chapter
    if session_id and session_id.strip():
        query_filter["session_id"] = session_id.strip()
    
    # Get total count
    total = await db[COLLECTIONS["mcq_sessions"]].count_documents(query_filter)
    
    # Fetch sessions
    sessions = await db[COLLECTIONS["mcq_sessions"]].find(query_filter)\
        .sort("created_at", -1)\
        .skip(skip)\
        .limit(limit)\
        .to_list(length=limit)
    
    session_responses = []
    for session in sessions:
        session_responses.append(SessionResponse(
            id=str(session["_id"]),
            session_id=session["session_id"],
            user_id=session.get("user_id"),
            subject=session["subject"],
            chapter=session["chapter"],
            generation_query=session.get("generation_query"),
            input_filename=session["input_filename"],
            input_type=session["input_type"],
            llm_provider=session["llm_provider"],
            model=session["model"],
            total_concepts_extracted=session["total_concepts_extracted"],
            total_mcqs_generated=session["total_mcqs_generated"],
            difficulty_distribution=session["difficulty_distribution"],
            first_attempt_summary=session.get("first_attempt_summary"),
            status=session["status"],
            created_at=session["created_at"],
            completed_at=session.get("completed_at")
        ))
    
    return SessionListResponse(
        total=total,
        sessions=session_responses
    )


@app.get("/sessions/{session_id}", response_model=SessionResponse, tags=["Sessions"])
async def get_session(session_id: str):
    """
    Get details of a specific MCQ generation session.
    """
    db = await get_async_database()
    
    session = await db[COLLECTIONS["mcq_sessions"]].find_one({"session_id": session_id})
        
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        id=str(session["_id"]),
        session_id=session["session_id"],
        user_id=session.get("user_id"),
        subject=session["subject"],
        chapter=session["chapter"],
        generation_query=session.get("generation_query"),
        input_filename=session["input_filename"],
        input_type=session["input_type"],
        llm_provider=session["llm_provider"],
        model=session["model"],
        total_concepts_extracted=session["total_concepts_extracted"],
        total_mcqs_generated=session["total_mcqs_generated"],
        difficulty_distribution=session["difficulty_distribution"],
        first_attempt_summary=session.get("first_attempt_summary"),
        status=session["status"],
        created_at=session["created_at"],
        completed_at=session.get("completed_at")
    )


@app.get("/mcqs", response_model=MCQListResponse, tags=["MCQs"])
async def list_mcqs(
    subject: Optional[str] = Query(None, description="Filter by subject"),
    chapter: Optional[str] = Query(None, description="Filter by chapter"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty (easy, medium, hard)"),
    skip: int = Query(0, ge=0, description="Number of MCQs to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum MCQs to return")
):
    """
    List all generated MCQs.
    
    Optionally filter by subject, chapter, session ID, and/or difficulty.
    """
    db = await get_async_database()
    
    # Build query filter
    query_filter = {}
    if subject:
        query_filter["subject"] = subject
    if chapter:
        query_filter["chapter"] = chapter
    if session_id:
        query_filter["session_id"] = session_id
    if difficulty:
        query_filter["metadata.difficulty"] = difficulty
    
    # Get total count
    total = await db[COLLECTIONS["mcqs"]].count_documents(query_filter)
    
    # Fetch MCQs
    mcqs = await db[COLLECTIONS["mcqs"]].find(query_filter)\
        .sort("question_number", 1)\
        .skip(skip)\
        .limit(limit)\
        .to_list(length=limit)
    
    mcq_responses = []
    for mcq in mcqs:
        mcq_responses.append(MCQResponse(
            id=str(mcq["_id"]),
            session_id=mcq["session_id"],
            subject=mcq["subject"],
            chapter=mcq["chapter"],
            question_number=mcq["question_number"],
            concept_id=mcq["concept_id"],
            stem=mcq["stem"],
            options=mcq["options"],
            correct_answer=mcq["correct_answer"],
            explanation=mcq["explanation"],
            answer_grading=mcq.get("answer_grading"),
            metadata=mcq["metadata"],
            created_at=mcq["created_at"]
        ))
    
    return MCQListResponse(
        total=total,
        mcqs=mcq_responses
    )


@app.get("/subjects", response_model=dict, tags=["Subjects"])
async def list_subjects():
    """
    Get list of all unique subjects in the database.
    
    Returns a list of subjects with their MCQ counts.
    """
    db = await get_async_database()
    
    # Get distinct subjects from sessions collection
    subjects = await db[COLLECTIONS["mcq_sessions"]].distinct("subject")
    
    # Get counts for each subject
    subject_stats = []
    for subject in subjects:
        session_count = await db[COLLECTIONS["mcq_sessions"]].count_documents({"subject": subject})
        mcq_count = await db[COLLECTIONS["mcqs"]].count_documents({"subject": subject})
        subject_stats.append({
            "subject": subject,
            "total_sessions": session_count,
            "total_mcqs": mcq_count
        })
    
    # Sort by subject name
    subject_stats.sort(key=lambda x: x["subject"])
    
    return {
        "total_subjects": len(subjects),
        "subjects": subject_stats
    }


@app.get("/mcqs/{mcq_id}", response_model=MCQResponse, tags=["MCQs"])
async def get_mcq(mcq_id: str):
    """
    Get details of a specific MCQ.
    """
    from bson import ObjectId
    
    db = await get_async_database()
    
    try:
        mcq = await db[COLLECTIONS["mcqs"]].find_one({"_id": ObjectId(mcq_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid MCQ ID format")
    
    if not mcq:
        raise HTTPException(status_code=404, detail="MCQ not found")
    
    return MCQResponse(
        id=str(mcq["_id"]),
        session_id=mcq["session_id"],
        subject=mcq["subject"],
        chapter=mcq["chapter"],
        question_number=mcq["question_number"],
        concept_id=mcq["concept_id"],
        stem=mcq["stem"],
        options=mcq["options"],
        correct_answer=mcq["correct_answer"],
        explanation=mcq["explanation"],
        answer_grading=mcq.get("answer_grading"),
        metadata=mcq["metadata"],
        created_at=mcq["created_at"]
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
