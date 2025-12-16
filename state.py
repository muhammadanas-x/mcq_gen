"""
State Schema for LangGraph MCQ Generator

Defines the typed state that flows through the graph nodes with batch processing
and loopback logic for concept-by-concept MCQ generation.
"""

from typing import TypedDict, List, Optional, Literal
from typing_extensions import NotRequired


class ConceptJSON(TypedDict):
    """Structured representation of a mathematical concept to generate MCQs from"""
    concept_id: str
    concept_name: str
    formula: str  # LaTeX format
    difficulty: Literal["easy", "medium", "hard"]
    prerequisites: List[str]
    context: str  # 2-3 sentences of explanation
    worked_example: NotRequired[Optional[str]]  # Optional worked problem


class StemWithAnswer(TypedDict):
    """Generated question stem with correct answer"""
    question_id: str
    concept_id: str
    stem: str  # Question text in markdown with LaTeX
    correct_answer: str  # LaTeX format
    difficulty: Literal["easy", "medium", "hard"]
    latex_valid: bool
    generation_metadata: NotRequired[dict]


class ValidatedQuestion(TypedDict):
    """Question that has passed mathematical validation"""
    question_id: str
    concept_id: str
    stem: str
    correct_answer: str
    difficulty: Literal["easy", "medium", "hard"]
    validation_score: float  # 0-1, confidence in correctness
    was_corrected: bool
    correction_details: NotRequired[Optional[str]]


class Distractor(TypedDict):
    """A plausible wrong answer with explanation"""
    option_text: str  # LaTeX format
    error_type: str  # From error taxonomy
    plausibility_score: float  # 0-1
    explanation: str  # Why this is wrong


class CompleteMCQ(TypedDict):
    """Final assembled MCQ with all components"""
    question_number: int
    concept_id: str
    stem: str
    options: dict[str, str]  # {"a": "...", "b": "...", "c": "...", "d": "..."}
    correct_answer: Literal["a", "b", "c", "d"]
    explanation: dict[str, str]  # {"correct": "...", "a": "...", "b": "...", etc}
    metadata: dict  # difficulty, concept, validation scores, etc


class MCQGeneratorState(TypedDict):
    """
    Main state object that flows through LangGraph nodes.
    
    Workflow:
    1. Analyzer populates concepts_queue and current_batch
    2. Stem Generator processes current_batch → generated_stems
       - If concepts_queue not empty, loads next batch and loops back
    3. Validator processes generated_stems → validated_questions
    4. Distractor Generator processes validated_questions → adds distractors
    5. Assembler creates final_mcqs
    """
    
    # Input
    input_source: str  # Path to chapter.md or existing MCQs
    input_type: Literal["chapter", "mcqs"]
    
    # Concept extraction and batch processing
    concepts_queue: List[ConceptJSON]  # Pending concepts to process
    processed_concept_ids: List[str]  # Track completed concepts
    current_batch: List[ConceptJSON]  # Current 10-15 concepts being processed
    batch_size: int  # Configurable batch size (default 10-15)
    
    # Generation pipeline
    generated_stems: List[StemWithAnswer]  # Questions with correct answers
    validated_questions: List[ValidatedQuestion]  # After SymPy validation
    questions_with_distractors: List[dict]  # Questions + distractors (pre-assembly)
    final_mcqs: List[CompleteMCQ]  # Complete MCQs ready for export
    
    # Routing and control flow
    needs_more_batches: bool  # True if concepts_queue not empty
    validation_failures: List[dict]  # Track removed questions for logging
    
    # Configuration
    config: dict  # LLM settings, output format, etc
    
    # Metrics and logging
    metrics: dict  # Track generation stats, validation rates, etc


# Helper type for routing decisions
class RouteDecision(TypedDict):
    next_node: str
    reason: str
