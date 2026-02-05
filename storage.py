"""
Storage Service for MongoDB Integration

Handles saving MCQ generation data to MongoDB Atlas without modifying
the existing MCQGenerator workflow.
"""

import uuid
from datetime import datetime
from typing import List, Dict
from database import get_sync_database, COLLECTIONS
from state import CompleteMCQ, ConceptJSON


class MCQStorageService:
    """
    Service for storing MCQ generation results in MongoDB.
    Works synchronously with the existing generator workflow.
    """
    
    def __init__(self, session_id: str = None):
        """
        Initialize storage service with a session ID.
        
        Args:
            session_id: Unique identifier for this generation session
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.db = get_sync_database()
    
    def save_session(
        self,
        subject: str,
        chapter: str,
        input_filename: str,
        input_type: str,
        llm_provider: str,
        model: str,
        batch_size: int,
        status: str = "processing"
    ) -> str:
        """
        Create a new session record in MongoDB.
        
        Args:
            subject: Subject name (e.g., "Calculus")
            chapter: Chapter name (e.g., "Chapter 3 - Definite Integrals")
            input_filename: Name of the input file
            input_type: "chapter" or "mcqs"
            llm_provider: LLM provider used
            model: Model name used
            batch_size: Batch size used
            status: Session status
        
        Returns:
            Session ID
        """
        session_doc = {
            "session_id": self.session_id,
            "subject": subject,
            "chapter": chapter,
            "input_filename": input_filename,
            "input_type": input_type,
            "llm_provider": llm_provider,
            "model": model,
            "batch_size": batch_size,
            "total_concepts_extracted": 0,
            "total_mcqs_generated": 0,
            "difficulty_distribution": {},
            "validation_rate": 0.0,
            "metrics": {},
            "status": status,
            "error_message": None,
            "created_at": datetime.utcnow(),
            "completed_at": None
        }
        
        self.db[COLLECTIONS["mcq_sessions"]].insert_one(session_doc)
        return self.session_id
    
    def save_concepts(self, concepts: List[ConceptJSON], subject: str, chapter: str):
        """
        Save extracted concepts to MongoDB.
        
        Args:
            concepts: List of ConceptJSON objects
            subject: Subject name
            chapter: Chapter name
        """
        if not concepts:
            return
        
        concept_docs = []
        for concept in concepts:
            doc = {
                "concept_id": concept["concept_id"],
                "concept_name": concept["concept_name"],
                "formula": concept["formula"],
                "difficulty": concept["difficulty"],
                "prerequisites": concept["prerequisites"],
                "context": concept["context"],
                "worked_example": concept.get("worked_example"),
                "session_id": self.session_id,
                "subject": subject,
                "chapter": chapter,
                "created_at": datetime.utcnow()
            }
            concept_docs.append(doc)
        
        self.db[COLLECTIONS["concepts"]].insert_many(concept_docs)
    
    def save_mcqs(self, mcqs: List[CompleteMCQ], subject: str, chapter: str):
        """
        Save generated MCQs to MongoDB.
        
        Args:
            mcqs: List of CompleteMCQ objects
            subject: Subject name
            chapter: Chapter name
        """
        if not mcqs:
            return
        
        mcq_docs = []
        for mcq in mcqs:
            doc = {
                "session_id": self.session_id,
                "subject": subject,
                "chapter": chapter,
                "question_number": mcq["question_number"],
                "concept_id": mcq["concept_id"],
                "stem": mcq["stem"],
                "options": mcq["options"],
                "correct_answer": mcq["correct_answer"],
                "explanation": mcq["explanation"],
                "metadata": mcq["metadata"],
                "created_at": datetime.utcnow()
            }
            mcq_docs.append(doc)
        
        self.db[COLLECTIONS["mcqs"]].insert_many(mcq_docs)
    
    def update_session(
        self,
        total_concepts: int = None,
        total_mcqs: int = None,
        difficulty_dist: Dict[str, int] = None,
        metrics: Dict = None,
        status: str = None,
        error_message: str = None
    ):
        """
        Update session with final metrics and status.
        
        Args:
            total_concepts: Total concepts extracted
            total_mcqs: Total MCQs generated
            difficulty_dist: Difficulty distribution
            metrics: Generation metrics
            status: Session status
            error_message: Error message if failed
        """
        update_doc = {}
        
        if total_concepts is not None:
            update_doc["total_concepts_extracted"] = total_concepts
        if total_mcqs is not None:
            update_doc["total_mcqs_generated"] = total_mcqs
        if difficulty_dist is not None:
            update_doc["difficulty_distribution"] = difficulty_dist
        if metrics is not None:
            update_doc["metrics"] = metrics
            update_doc["validation_rate"] = metrics.get("validation_rate", 0.0)
        if status is not None:
            update_doc["status"] = status
            if status == "completed":
                update_doc["completed_at"] = datetime.utcnow()
        if error_message is not None:
            update_doc["error_message"] = error_message
        
        if update_doc:
            self.db[COLLECTIONS["mcq_sessions"]].update_one(
                {"session_id": self.session_id},
                {"$set": update_doc}
            )
