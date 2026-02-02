# MCQ Generator with LangGraph

A sophisticated MCQ generator that uses cognitive error modeling and multi-stage validation to create high-quality multiple-choice questions for calculus/integration topics.

**Now available as a REST API with MongoDB Atlas storage!**

## Features

- **Loopback Architecture**: Batch processes concepts (10-15 at a time) for efficient generation
- **Content Analyzer**: Extracts concepts from chapters or existing MCQs into structured JSON
- **Stem Generator**: Creates questions with correct answers, preventing hallucination through focused prompting
- **Mathematical Validator**: Uses SymPy to verify correctness via differentiation
- **Distractor Generator**: Applies cognitive error taxonomy for plausible wrong options
- **MCQ Assembly**: Produces formatted output with explanations
- **REST API**: FastAPI server with MongoDB Atlas integration
- **Database Storage**: Persistent storage of MCQs, concepts, and generation sessions

## Quick Start

### Option 1: REST API (Recommended)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with MongoDB Atlas URI and LLM API key
```

3. Start the API server:
```bash
python start_server.py
```

4. Access the API:
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

5. Generate MCQs via API:
```bash
curl -X POST "http://localhost:8000/generate-mcqs" \
  -F "file=@chapter3.md" \
  -F "input_type=chapter"
```

See [API_README.md](API_README.md) for complete API documentation.

### Option 2: CLI

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure API keys:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Run the generator:
```bash
python main.py --input ../chapter3.md --output generated_mcqs.md --batch-size 10
```

## Architecture

```
Input (Chapter/MCQs)
    ↓
Content Analyzer → Concepts Queue (JSON objects)
    ↓
Stem Generator (batch 10-15) ──┐
    ↓                           │
Validator (SymPy check)         │ Loop until
    ↓                           │ queue empty
[More concepts?] ───────────────┘
    ↓ No
Distractor Generator (3-5 per question)
    ↓
MCQ Assembly (with explanations)
    ↓
Output (Formatted MCQs)
```

## Project Structure

### Core Components
- `state.py`: LangGraph state schema definitions
- `nodes/`: Individual node implementations
  - `analyzer.py`: Content extraction and concept parsing
  - `stem_generator.py`: Question and answer generation
  - `validator.py`: Mathematical correctness verification
  - `distractor_generator.py`: Cognitive error-based distractors
  - `assembler.py`: Final MCQ formatting
- `graph.py`: LangGraph orchestration and routing logic
- `error_taxonomy.py`: Systematic error patterns for distractors
- `utils/`: Helper functions (LaTeX validation, SymPy integration)
- `main.py`: CLI entry point

### API Components
- `server.py`: FastAPI application with REST endpoints
- `database.py`: MongoDB connection and configuration
- `models.py`: Pydantic models for API requests/responses
- `storage.py`: MongoDB storage service for MCQs
- `start_server.py`: Server startup script with health checks
- `test_api.py`: API testing script

## Example Usage

### CLI Example

```python
from main import MCQGenerator

generator = MCQGenerator(
    llm_provider="gemini",  # or "anthropic", "openai"
    model="gemini-2.5-pro",
    batch_size=15
)

mcqs = generator.generate_from_file(
    input_path="chapter3.md",
    input_type="chapter",
    output_path="generated_mcqs.md"
)
```

### API Example

```python
import requests

url = "http://localhost:8000/generate-mcqs"

with open("chapter3.md", "rb") as f:
    files = {"file": ("chapter3.md", f)}
    data = {"input_type": "chapter"}
    
    response = requests.post(url, files=files, data=data)
    result = response.json()
    
    print(f"Generated {result['total_mcqs_generated']} MCQs")
    print(f"Session ID: {result['session_id']}")
```

## API Endpoints

- `POST /generate-mcqs` - Generate MCQs from uploaded file
- `GET /sessions` - List all generation sessions
- `GET /sessions/{session_id}` - Get session details
- `GET /mcqs` - List all MCQs (filterable by session)
- `GET /mcqs/{mcq_id}` - Get specific MCQ details
- `GET /health` - Health check endpoint

See [API_README.md](API_README.md) for complete documentation.

## MongoDB Collections

- **mcq_sessions**: Generation session metadata
- **mcqs**: Individual MCQ documents
- **concepts**: Extracted concept data
