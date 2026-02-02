# MCQ Generator API - Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT APPLICATIONS                          │
│  (Browser, Mobile App, Python Script, cURL, Postman, etc.)         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ HTTP/HTTPS Requests
                             │ (multipart/form-data)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FASTAPI SERVER (server.py)                      │
├─────────────────────────────────────────────────────────────────────┤
│  Endpoints:                                                          │
│  • POST /generate-mcqs    - Upload file, generate MCQs             │
│  • GET  /sessions         - List all sessions                       │
│  • GET  /sessions/{id}    - Get session details                    │
│  • GET  /mcqs             - List MCQs (filterable)                 │
│  • GET  /mcqs/{id}        - Get MCQ details                        │
│  • GET  /health           - Health check                           │
│  • GET  /                 - API info                               │
├─────────────────────────────────────────────────────────────────────┤
│  Components:                                                         │
│  • Request validation (Pydantic models)                            │
│  • File upload handling                                            │
│  • Error handling & logging                                        │
│  • CORS middleware                                                 │
└────────┬──────────────────────────────────┬─────────────────────────┘
         │                                  │
         │                                  │
         ▼                                  ▼
┌─────────────────────────┐      ┌──────────────────────────┐
│   STORAGE SERVICE       │      │   DATABASE LAYER         │
│   (storage.py)          │◄────►│   (database.py)          │
├─────────────────────────┤      ├──────────────────────────┤
│ • MCQStorageService     │      │ • MongoDB connections    │
│ • save_session()        │      │   - Async (Motor)        │
│ • save_concepts()       │      │   - Sync (PyMongo)       │
│ • save_mcqs()           │      │ • Connection pooling     │
│ • update_session()      │      │ • Database operations    │
└────────┬────────────────┘      └──────────┬───────────────┘
         │                                  │
         │                                  │
         ▼                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    MCQ GENERATOR (main.py)                           │
│                    [ORIGINAL LOGIC - UNCHANGED]                      │
├─────────────────────────────────────────────────────────────────────┤
│  • MCQGenerator class                                               │
│  • generate_from_file()                                             │
│  • Orchestrates entire workflow                                     │
└────────┬────────────────────────────────────────────────────────────┘
         │
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH WORKFLOW (graph.py)                     │
│                    [ORIGINAL LOGIC - UNCHANGED]                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐                                              │
│  │  Content         │  Extracts concepts from input                │
│  │  Analyzer        │  Returns: ConceptJSON objects                │
│  └────────┬─────────┘                                              │
│           │                                                         │
│           ▼                                                         │
│  ┌──────────────────┐                                              │
│  │  Stem            │  Generates questions (batch 10-15)           │
│  │  Generator       │  Returns: StemWithAnswer objects             │
│  └────────┬─────────┘                                              │
│           │                                                         │
│           ▼                                                         │
│     [LOOPBACK?] ──Yes──► (Process next batch)                      │
│           │                                                         │
│           No                                                        │
│           │                                                         │
│           ▼                                                         │
│  ┌──────────────────┐                                              │
│  │  Validator       │  Validates LaTeX syntax                      │
│  │                  │  Returns: ValidatedQuestion objects          │
│  └────────┬─────────┘                                              │
│           │                                                         │
│           ▼                                                         │
│  ┌──────────────────┐                                              │
│  │  Distractor      │  Creates wrong answers (5 → top 3)          │
│  │  Generator       │  Uses error taxonomy                         │
│  └────────┬─────────┘  Returns: Questions with distractors         │
│           │                                                         │
│           ▼                                                         │
│  ┌──────────────────┐                                              │
│  │  Assembler       │  Shuffles options, formats output           │
│  │                  │  Returns: CompleteMCQ objects                │
│  └──────────────────┘                                              │
│                                                                      │
└────────┬─────────────────────────────────────────────────────────┬─┘
         │                                                         │
         ▼                                                         ▼
┌─────────────────────┐                              ┌──────────────────┐
│  ERROR TAXONOMY     │                              │  UTILITY MODULES │
│  (error_taxonomy.py)│                              │  (utils/)        │
├─────────────────────┤                              ├──────────────────┤
│ • 13 error types    │                              │ • LaTeX validator│
│ • Categorized       │                              │ • SymPy validator│
│ • Plausibility      │                              │                  │
└─────────────────────┘                              └──────────────────┘


DATA FLOW:
──────────

1. Client uploads .md file
2. FastAPI receives request
3. Storage service creates session record
4. MCQGenerator processes file (unchanged logic)
5. LangGraph executes workflow:
   - Analyzer → extracts concepts
   - Stem Generator → creates questions (with loopback)
   - Validator → checks validity
   - Distractor Generator → adds wrong answers
   - Assembler → formats MCQs
6. Storage service saves all data to MongoDB
7. FastAPI returns results to client


MONGODB COLLECTIONS:
────────────────────

┌──────────────────────────────────────────────────────────────────┐
│                         MONGODB ATLAS                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │  mcq_sessions     │  │     mcqs     │  │    concepts     │  │
│  ├───────────────────┤  ├──────────────┤  ├─────────────────┤  │
│  │ • session_id      │  │ • session_id │  │ • session_id    │  │
│  │ • input_filename  │  │ • question_# │  │ • concept_id    │  │
│  │ • input_type      │  │ • stem       │  │ • concept_name  │  │
│  │ • llm_provider    │  │ • options    │  │ • formula       │  │
│  │ • model           │  │ • correct    │  │ • difficulty    │  │
│  │ • batch_size      │  │ • explanation│  │ • context       │  │
│  │ • total_concepts  │  │ • metadata   │  │ • example       │  │
│  │ • total_mcqs      │  │ • created_at │  │ • created_at    │  │
│  │ • difficulty_dist │  └──────────────┘  └─────────────────┘  │
│  │ • status          │                                          │
│  │ • created_at      │   One-to-Many        One-to-Many        │
│  │ • completed_at    │   relationship       relationship       │
│  └───────────────────┘                                          │
│         1 session → many MCQs → many concepts                   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘


TECHNOLOGY STACK:
─────────────────

• Web Framework: FastAPI 0.104+
• ASGI Server: Uvicorn
• Database: MongoDB Atlas (cloud)
• DB Drivers: Motor (async) + PyMongo (sync)
• Validation: Pydantic 2.5+
• AI/ML: LangChain, LangGraph
• LLM Providers: Gemini, Claude, OpenAI
• Math Processing: SymPy, PyLatexEnc


KEY DESIGN DECISIONS:
─────────────────────

✓ Synchronous API: Waits for generation to complete
✓ File Upload: Multipart form-data support
✓ Dual DB Clients: Async for API, Sync for generator
✓ Storage Wrapper: Non-invasive integration
✓ Zero Modifications: Original logic preserved
✓ Comprehensive Docs: API, setup, examples
✓ Production Ready: Error handling, logging, cleanup
```
