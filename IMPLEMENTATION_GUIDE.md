# MCQ Generator Implementation Guide

## Quick Start

### 1. Install Dependencies
```bash
cd mcq_generator
pip install -r requirements.txt
```

### 2. Configure API Keys
```bash
cp .env.example .env
# Edit .env and add your API key (Anthropic or OpenAI)
```

### 3. Test Components
```bash
python test_components.py
```

### 4. Generate MCQs

#### Option A: From chapter content
```bash
python main.py \
  --input ../chapter3.md \
  --input-type chapter \
  --output generated_mcqs.md \
  --llm gemini \
  --batch-size 15
```

#### Option B: From existing MCQs
```bash
python main.py \
  --input ../chap3_fung_mcqs.md \
  --input-type mcqs \
  --output generated_mcqs.md \
  --llm gemini \
  --batch-size 15
```

## Architecture Overview

### LangGraph Flow with Loopback

```
┌─────────────────┐
│  Content        │  Extracts 40-50 concepts as JSON objects
│  Analyzer       │  Populates concepts_queue
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Stem           │  Processes batch of 10-15 concepts
│  Generator      │  Generates question + correct answer
└────────┬────────┘
         │
         ▼
    ┌────────┐
    │ Queue  │  Yes → Load next batch, LOOP BACK ↑
    │ Empty? │
    └────┬───┘
         │ No
         ▼
┌─────────────────┐
│  Validator      │  SymPy verification via differentiation
│  (SymPy)        │  Corrects or removes wrong answers
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Distractor     │  Generates 5 distractors per question
│  Generator      │  Applies cognitive error taxonomy
└────────┬────────┘  Ranks by plausibility, selects top 3
         │
         ▼
┌─────────────────┐
│  Assembler      │  Shuffles options (a,b,c,d)
│                 │  Adds explanations
└────────┬────────┘  Exports formatted markdown
         │
         ▼
    Final MCQs
```

## Key Features

### 1. Cognitive Error Modeling
- **13 error types** categorized into:
  - Algebraic (sign flip, coefficient error, exponent off-by-one)
  - Calculus-specific (chain rule forgotten, wrong formula, integration by parts)
  - Trigonometric (identity confusion, inverse function error)
  - Notational (absolute value missing, constant omitted)
  - Conceptual (derivative instead of integral, property misapplication)

### 2. Multi-Stage Validation
- **Syntactic**: LaTeX parser checks for balanced braces, valid commands
- **Semantic**: SymPy differentiates answer to verify it matches integrand
- **Pedagogical**: Scores distractor plausibility and diversity

### 3. Batch Processing with Loopback
- Processes concepts in batches of 10-15 to prevent hallucination
- Automatically loops back until all concepts processed
- State persisted between iterations

## Project Structure

```
mcq_generator/
├── state.py                    # LangGraph state schema (TypedDict)
├── error_taxonomy.py           # 13 error types with descriptions
├── graph.py                    # LangGraph orchestration + routing
├── main.py                     # CLI entry point
│
├── nodes/
│   ├── analyzer.py            # Extracts concepts from input
│   ├── stem_generator.py      # Generates questions + answers
│   ├── validator.py           # SymPy mathematical verification
│   ├── distractor_generator.py # Creates wrong options
│   └── assembler.py           # Formats final MCQs
│
├── utils/
│   ├── latex_validator.py     # LaTeX syntax checking
│   └── sympy_validator.py     # Symbolic math validation
│
├── test_components.py         # Unit tests for components
├── examples.py                # Usage examples
├── requirements.txt           # Dependencies
└── README.md                  # Documentation
```

## Configuration Options

### Batch Size
- **Small (5-10)**: Faster, more iterations, good for testing
- **Medium (10-15)**: Recommended for production
- **Large (15-20)**: Fewer iterations, higher context usage

### LLM Provider
- **Google Gemini 2.0 Flash**: Fast, cost-effective, good mathematical reasoning (default)
- **Anthropic Claude 3.5 Sonnet**: Excellent for mathematical reasoning
- **OpenAI GPT-4**: Strong alternative performance

### Difficulty Distribution
Controlled by concept extraction, typically:
- Easy: 30% (direct formula application)
- Medium: 50% (one-step problem solving)
- Hard: 20% (multi-step, synthesis)

## Validation Metrics

The system tracks:
- **Generation success rate**: % of concepts that produce valid questions
- **Validation pass rate**: % of questions verified correct by SymPy
- **Correction rate**: % of questions auto-corrected by SymPy
- **Distractor quality**: Average plausibility score
- **Difficulty distribution**: Breakdown by easy/medium/hard

## Tips for Impressive FYP Presentation

### 1. Demonstrate Robustness
- Show validation catching incorrect LLM answers
- Display correction in action (wrong answer → SymPy corrects it)
- Compare distractor quality: random vs cognitive-error-based

### 2. Highlight Novel Contributions
- **Error taxonomy**: Systematic categorization of 13 integration mistakes
- **Loopback architecture**: Batch processing prevents hallucination
- **Multi-stage validation**: LaTeX + SymPy + plausibility scoring

### 3. Provide Evaluation
- Generate 50 MCQs, have professors rate them (1-5 scale)
- Compare against baseline: pure GPT-4 (no validation)
- Measure: correctness rate, distractor effectiveness, novelty

### 4. Show Failure Cases
- Demonstrate what happens when validation fails
- Show questions that were removed (with reasons)
- Discuss limitations (complex nested integrals, definite integrals with limits)

### 5. Future Work
- Expand to other calculus topics (derivatives, series, differential equations)
- Add human-in-the-loop feedback collection
- Train distractor ranking model from student response data
- Support multiple difficulty levels per concept

## Troubleshooting

### Issue: LaTeX validation fails frequently
- Check that LLM is using correct notation (\\sin not sin)
- Verify \\frac{}{} has two arguments
- Ensure balanced braces

### Issue: SymPy can't verify answers
- Some complex integrals may not simplify to 0
- Try expanding/factoring the difference
- May need to add manual verification rules

### Issue: Distractors too obvious
- Increase plausibility threshold
- Add more error types to taxonomy
- Use higher temperature for distractor generation

### Issue: Running out of API credits
- Use smaller batch sizes for testing
- Test with sample file (5-10 concepts)
- Cache intermediate results

## Next Steps

1. **Run tests**: `python test_components.py`
2. **Try examples**: Edit `examples.py` and uncomment an example
3. **Generate small batch**: Start with 5 concepts to verify setup
4. **Full generation**: Run with full chapter (40-50 concepts)
5. **Evaluate quality**: Have professor review sample MCQs
6. **Iterate**: Refine based on feedback

## Contact & Support

For questions about the implementation:
- Check existing MCQ patterns in `../chap3_fung_mcqs.md`
- Review error taxonomy in `error_taxonomy.py`
- Test individual components with `test_components.py`
