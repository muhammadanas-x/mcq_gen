# MCQ Generator with LangGraph

A sophisticated MCQ generator that uses cognitive error modeling and multi-stage validation to create high-quality multiple-choice questions for calculus/integration topics.

## Features

- **Loopback Architecture**: Batch processes concepts (10-15 at a time) for efficient generation
- **Content Analyzer**: Extracts concepts from chapters or existing MCQs into structured JSON
- **Stem Generator**: Creates questions with correct answers, preventing hallucination through focused prompting
- **Mathematical Validator**: Uses SymPy to verify correctness via differentiation
- **Distractor Generator**: Applies cognitive error taxonomy for plausible wrong options
- **MCQ Assembly**: Produces formatted output with explanations

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

## Example

```python
from mcq_generator import MCQGenerator

generator = MCQGenerator(
    llm_provider="gemini",  # or "anthropic", "openai"
    model="gemini-2.5-pro",
    batch_size=15
)

mcqs = generator.generate_from_file(
    input_path="chapter3.md",
    num_questions=30,
    difficulty_mix={"easy": 0.3, "medium": 0.5, "hard": 0.2}
)

generator.export(mcqs, "output.md", format="markdown")
```
