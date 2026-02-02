# MongoDB Database Schema

## Collections Overview

The MCQ Generator uses 3 main collections in MongoDB Atlas:

---

## 1. `mcq_sessions` Collection

**Purpose**: Stores metadata about each MCQ generation session

### Schema
```javascript
{
  _id: ObjectId,                    // Auto-generated MongoDB ID
  session_id: String,               // UUID for session
  subject: String,                  // Subject name (e.g., "Calculus", "Integration")
  input_filename: String,           // Uploaded file name
  input_type: String,               // "chapter" or "mcqs"
  llm_provider: String,             // "gemini", "anthropic", or "openai"
  model: String,                    // Model name (e.g., "gemini-2.5-pro")
  batch_size: Number,               // Concepts per batch
  total_concepts_extracted: Number, // Total concepts found
  total_mcqs_generated: Number,     // Total MCQs created
  difficulty_distribution: {        // MCQ difficulty breakdown
    easy: Number,
    medium: Number,
    hard: Number
  },
  validation_rate: Number,          // Validation success rate (0-1)
  metrics: Object,                  // Additional metrics
  status: String,                   // "processing", "completed", or "failed"
  error_message: String?,           // Error if failed (optional)
  created_at: ISODate,              // Session start time
  completed_at: ISODate?            // Session end time (optional)
}
```

### Indexes
- `session_id` (unique)
- `subject` (for filtering by subject)
- `status` (for filtering by status)
- `created_at` (for sorting)

### Example Document
```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "subject": "Calculus - Integration Techniques",
  "input_filename": "chapter3_integration.md",
  "input_type": "chapter",
  "llm_provider": "gemini",
  "model": "gemini-2.5-pro",
  "batch_size": 15,
  "total_concepts_extracted": 45,
  "total_mcqs_generated": 45,
  "difficulty_distribution": {
    "easy": 15,
    "medium": 25,
    "hard": 5
  },
  "validation_rate": 1.0,
  "metrics": {
    "stems_generated": 45,
    "questions_validated": 45,
    "total_distractors_generated": 135
  },
  "status": "completed",
  "error_message": null,
  "created_at": ISODate("2026-02-03T10:30:00.000Z"),
  "completed_at": ISODate("2026-02-03T10:35:22.000Z")
}
```

---

## 2. `mcqs` Collection

**Purpose**: Stores individual MCQ documents

### Schema
```javascript
{
  _id: ObjectId,                    // Auto-generated MongoDB ID
  session_id: String,               // Reference to parent session
  subject: String,                  // Subject name (for easy filtering)
  question_number: Number,          // Question number in sequence
  concept_id: String,               // Related concept ID
  stem: String,                     // Question text (with LaTeX)
  options: {                        // Answer options
    a: String,                      // Option A (LaTeX)
    b: String,                      // Option B (LaTeX)
    c: String,                      // Option C (LaTeX)
    d: String                       // Option D (LaTeX)
  },
  correct_answer: String,           // Correct option key ("a", "b", "c", "d")
  explanation: {                    // Explanations for each option
    correct: String,                // Why correct answer is right
    a: String,                      // Explanation for option A
    b: String,                      // Explanation for option B
    c: String,                      // Explanation for option C
    d: String                       // Explanation for option D
  },
  metadata: {                       // Additional metadata
    difficulty: String,             // "easy", "medium", or "hard"
    validation_score: Number,       // Validation confidence (0-1)
    was_corrected: Boolean,         // Whether answer was corrected
    integral_type: String           // Type of integral (e.g., "substitution")
  },
  created_at: ISODate               // Creation timestamp
}
```

### Indexes
- `session_id` (for querying by session)
- `subject` (for filtering by subject)
- `metadata.difficulty` (for filtering by difficulty)
- `question_number` (for sorting)

### Example Document
```json
{
  "_id": ObjectId("507f1f77bcf86cd799439012"),
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "subject": "Calculus - Integration Techniques",
  "question_number": 1,
  "concept_id": "u_substitution",
  "stem": "Find $\\int 2x(x^2 + 3)^4 dx$",
  "options": {
    "a": "$\\frac{(x^2+3)^5}{5} + c$",
    "b": "$(x^2+3)^5 + c$",
    "c": "$\\frac{(x^2+3)^5}{10} + c$",
    "d": "$2x(x^2+3)^5 + c$"
  },
  "correct_answer": "a",
  "explanation": {
    "correct": "This is the correct answer. Use u-substitution with u = x^2 + 3",
    "a": "Correct! Using u-substitution: u = x^2+3, du = 2x dx, so ∫u^4 du = u^5/5 + c",
    "b": "This error occurs when forgetting to divide by 5 after integrating u^4",
    "c": "This error happens when incorrectly dividing by 10 instead of 5",
    "d": "This mistake keeps the 2x factor instead of recognizing it as part of du"
  },
  "metadata": {
    "difficulty": "medium",
    "validation_score": 1.0,
    "was_corrected": false,
    "integral_type": "substitution"
  },
  "created_at": ISODate("2026-02-03T10:32:15.000Z")
}
```

---

## 3. `concepts` Collection

**Purpose**: Stores extracted mathematical concepts

### Schema
```javascript
{
  _id: ObjectId,                    // Auto-generated MongoDB ID
  session_id: String,               // Reference to parent session
  subject: String,                  // Subject name
  concept_id: String,               // Unique concept identifier
  concept_name: String,             // Human-readable name
  formula: String,                  // LaTeX formula
  difficulty: String,               // "easy", "medium", or "hard"
  prerequisites: [String],          // List of prerequisite concept IDs
  context: String,                  // Explanation text (2-3 sentences)
  worked_example: String?,          // Optional worked problem (optional)
  created_at: ISODate               // Creation timestamp
}
```

### Indexes
- `session_id` (for querying by session)
- `subject` (for filtering by subject)
- `concept_id` (for lookups)
- `difficulty` (for filtering)

### Example Document
```json
{
  "_id": ObjectId("507f1f77bcf86cd799439013"),
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "subject": "Calculus - Integration Techniques",
  "concept_id": "u_substitution",
  "concept_name": "U-Substitution Method",
  "formula": "\\int f(g(x))g'(x)dx = \\int f(u)du",
  "difficulty": "medium",
  "prerequisites": ["chain_rule", "power_rule_integration"],
  "context": "This technique reverses the chain rule and is used when the integrand is a composite function with its derivative present. It simplifies complex integrals by substituting u for an inner function.",
  "worked_example": "Problem: Find \\int 2x(x^2+1)^5 dx.\nSolution: Let u = x^2 + 1, du = 2x dx, then \\int u^5 du = \\frac{u^6}{6} + C = \\frac{(x^2+1)^6}{6} + C.",
  "created_at": ISODate("2026-02-03T10:31:45.000Z")
}
```

---

## Relationships

```
mcq_sessions (1) ──────► (Many) mcqs
     │                            │
     │                            └─ Filtered by session_id, subject
     │
     └──────────────────► (Many) concepts
                                  │
                                  └─ Filtered by session_id, subject
```

---

## Queries by Subject

### Get all sessions for a subject
```javascript
db.mcq_sessions.find({ subject: "Calculus - Integration Techniques" })
```

### Get all MCQs for a subject
```javascript
db.mcqs.find({ subject: "Calculus - Integration Techniques" })
```

### Get MCQ count by subject and difficulty
```javascript
db.mcqs.aggregate([
  { $match: { subject: "Calculus - Integration Techniques" } },
  { $group: {
      _id: "$metadata.difficulty",
      count: { $sum: 1 }
    }
  }
])
```

### Get all concepts for a subject
```javascript
db.concepts.find({ subject: "Calculus - Integration Techniques" })
```

### List all subjects
```javascript
db.mcq_sessions.distinct("subject")
```

---

## Storage Estimates

### Per Session (approximate)
- Session document: ~500 bytes
- Concepts (30-50): ~50-80 KB
- MCQs (30-50): ~100-150 KB

### Total per session: ~150-230 KB

### For 100 sessions: ~15-23 MB

MongoDB Atlas free tier (512 MB) can handle hundreds of sessions easily.
