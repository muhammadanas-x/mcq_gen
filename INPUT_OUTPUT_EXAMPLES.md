# MCQ Generator - Input & Output Examples

This document shows what the input and output look like at each stage of the MCQ generation process.

---

## 📥 **INPUT FORMATS**

The system accepts two types of input:

### **Option 1: Chapter Content** (`input_type="chapter"`)

Example chapter markdown file:

```markdown
# Chapter 3: Integration Techniques

## 3.1 Power Rule for Integration

The power rule for integration states that:

$$\int x^n dx = \frac{x^{n+1}}{n+1} + C, \quad n \neq -1$$

This is one of the most fundamental integration formulas.

**Example:** Find $\int x^4 dx$

Solution: Using the power rule with $n=4$:
$$\int x^4 dx = \frac{x^5}{5} + C$$

## 3.2 Integration by Substitution

The u-substitution method is used when...

$$\int f(g(x))g'(x)dx = \int f(u)du$$

**Example:** Find $\int 2x(x^2+1)^5 dx$

Let $u = x^2 + 1$, then $du = 2x dx$...
```

### **Option 2: Existing MCQs** (`input_type="mcqs"`)

Example MCQ markdown file:

```markdown
### Practice Exercise

**1. What is $\int x^4 dx = ?$**
   *   (a) $\frac{x^5}{5} + c$
   *   (b) $\frac{x^3}{3} + c$
   *   (c) $4x^3 + c$
   *   (d) $x^5 + c$

**2. Find $\int \frac{1}{x} dx$**
   *   (a) $\ln|x| + c$
   *   (b) $\frac{1}{x^2} + c$
   *   (c) $-\frac{1}{x^2} + c$
   *   (d) $x\ln x + c$
```

---

## 🔄 **INTERMEDIATE OUTPUTS**

### **Stage 1: Content Analyzer Output** (`intermediate_data/01_concepts.json`)

The analyzer extracts structured concepts as JSON:

```json
[
  {
    "concept_id": "power_rule_integration",
    "concept_name": "Power Rule for Integration",
    "formula": "\\int x^n dx = \\frac{x^{n+1}}{n+1} + C, \\text{ for } n \\neq -1",
    "difficulty": "easy",
    "prerequisites": [],
    "context": "This is the fundamental rule for finding the antiderivative of a variable raised to a constant power.",
    "worked_example": "Problem: Find \\int x^4 dx.\nSolution: Using the power rule with n=4, we get \\frac{x^5}{5} + C."
  },
  {
    "concept_id": "u_substitution",
    "concept_name": "U-Substitution Method",
    "formula": "\\int f(g(x))g'(x)dx = \\int f(u)du",
    "difficulty": "medium",
    "prerequisites": ["chain_rule", "power_rule_integration"],
    "context": "This technique reverses the chain rule and is used when the integrand is a composite function with its derivative present.",
    "worked_example": "Problem: Find \\int 2x(x^2+1)^5 dx.\nSolution: Let u = x^2 + 1, du = 2x dx, then \\int u^5 du = \\frac{u^6}{6} + C = \\frac{(x^2+1)^6}{6} + C."
  }
]
```

**Readable format** (`intermediate_data/01_concepts_readable.txt`):

```
================================================================================
CONTENT ANALYZER - EXTRACTED CONCEPTS
================================================================================
Timestamp: 2025-12-16 20:54:50
Input Source: ../chap3_fung_mcqs.md
Input Type: mcqs
Total Concepts Extracted: 30

DIFFICULTY DISTRIBUTION:
  EASY: 12 concepts
  MEDIUM: 17 concepts
  HARD: 1 concepts

================================================================================
CONCEPT 1: Power Rule for Integration
================================================================================
ID: power_rule_integration
Difficulty: easy

Context:
This is the fundamental rule for finding the antiderivative of a variable 
raised to a constant power.

Formula:
\int x^n dx = \frac{x^{n+1}}{n+1} + C, \text{ for } n \neq -1

Worked Example:
Problem: Find \int x^4 dx.
Solution: Using the power rule with n=4, we get \frac{x^5}{5} + C.
```

### **Stage 2: Stem Generator Output** (internal state)

For each concept, generates a question with correct answer:

```python
{
  "question_id": "uuid-1234-5678-abcd",
  "concept_id": "u_substitution",
  "stem": "Find $\\int 2x(x^2 + 3)^4 dx$",
  "correct_answer": "$\\frac{(x^2+3)^5}{5} + c$",
  "difficulty": "medium",
  "latex_valid": true,
  "generation_metadata": {
    "integral_type": "substitution",
    "reasoning": "Use u-substitution with u = x^2 + 3"
  }
}
```

### **Stage 3: Validator Output** (internal state)

Currently passes all LaTeX-valid questions through:

```python
{
  "question_id": "uuid-1234-5678-abcd",
  "concept_id": "u_substitution",
  "stem": "Find $\\int 2x(x^2 + 3)^4 dx$",
  "correct_answer": "$\\frac{(x^2+3)^5}{5} + c$",
  "difficulty": "medium",
  "validation_score": 1.0,
  "was_corrected": false
}
```

### **Stage 4: Distractor Generator Output** (internal state)

Adds 3 plausible wrong answers:

```python
{
  "question_id": "uuid-1234-5678-abcd",
  "stem": "Find $\\int 2x(x^2 + 3)^4 dx$",
  "correct_answer": "$\\frac{(x^2+3)^5}{5} + c$",
  "distractors": [
    {
      "option_text": "$\\frac{(x^2+3)^5}{10} + c$",
      "error_type": "coefficient_error",
      "plausibility_score": 0.85,
      "explanation": "This error occurs when the student forgets to account for the 2x factor from differentiation, incorrectly dividing by 10 instead of 5."
    },
    {
      "option_text": "$(x^2+3)^5 + c$",
      "error_type": "chain_rule_forgotten",
      "plausibility_score": 0.78,
      "explanation": "This error happens when the student forgets to divide by the derivative of the inner function (2x)."
    },
    {
      "option_text": "$\\frac{2x(x^2+3)^5}{5} + c$",
      "error_type": "wrong_formula",
      "plausibility_score": 0.72,
      "explanation": "Student incorrectly keeps the 2x factor outside instead of recognizing it as part of the substitution."
    }
  ]
}
```

---

## 📤 **FINAL OUTPUT** (`generated_mcqs.md`)

The assembler shuffles options and creates formatted markdown:

```markdown
### Generated MCQs: Integration
#### PRACTICE EXERCISE

**1. Find $\int 2x(x^2 + 3)^4 dx$**
   *   (a) $(x^2+3)^5 + c$
   *   (b) $\frac{2x(x^2+3)^5}{5} + c$
   *   **(c) $\frac{(x^2+3)^5}{5} + c$**
   *   (d) $\frac{(x^2+3)^5}{10} + c$

   **Explanation:**
   - **Correct (c):** This is the correct answer. Use u-substitution with u = x^2 + 3
   - **(a):** This error happens when the student forgets to divide by the derivative of the inner function (2x).
   - **(b):** Student incorrectly keeps the 2x factor outside instead of recognizing it as part of the substitution.
   - **(d):** This error occurs when the student forgets to account for the 2x factor from differentiation, incorrectly dividing by 10 instead of 5.

**2. What is $\int \sin(x) dx = ?$**
   *   (a) $\cos(x) + c$
   *   **(b) $-\cos(x) + c$**
   *   (c) $-\sin(x) + c$
   *   (d) $\frac{\sin^2(x)}{2} + c$

   **Explanation:**
   - **Correct (b):** This is the correct answer. The antiderivative of sine is negative cosine.
   - **(a):** This is a common sign error, forgetting the negative sign in the antiderivative.
   - **(c):** This error occurs when confusing the derivative with the integral of sine.
   - **(d):** This applies the wrong integration formula entirely.

**3. Find $\int \frac{1}{x} dx$**
   *   **(a) $\ln|x| + c$**
   *   (b) $\ln(x) + c$
   *   (c) $\frac{1}{x^2} + c$
   *   (d) $-\frac{1}{x^2} + c$

   **Explanation:**
   - **Correct (a):** This is the correct answer. The integral of 1/x requires absolute value bars.
   - **(b):** Missing absolute value bars in the logarithm - important for negative x values.
   - **(c):** This is the derivative of 1/x, not the integral.
   - **(d):** This is the derivative of 1/x with a sign error.

---

**Generated Questions:** 3
**Difficulty Distribution:**
- Easy: 2 questions
- Medium: 1 questions
```

---

## 📊 **CONSOLE OUTPUT DURING GENERATION**

When running the generator, you'll see:

```
============================================================
MCQ GENERATOR - Starting Generation
============================================================
Input: ../chapter3.md (chapter)
LLM: gemini - gemini-2.5-pro
Batch size: 15
============================================================

Executing LangGraph workflow...

============================================================
CONTENT ANALYZER NODE
============================================================
Analyzing chapter content from: ../chapter3.md
Extracted 45 concepts

Concept 1: Power Rule for Integration (easy)
  Formula: \int x^n dx = \frac{x^{n+1}}{n+1} + C...

Prepared first batch of 15 concepts
Remaining in queue: 30

Saved intermediate data:
  - intermediate_data/01_concepts.json
  - intermediate_data/01_concepts_readable.txt

============================================================
STEM GENERATOR NODE
============================================================
Processing batch of 15 concepts

[1/15] Generating question for: Power Rule for Integration
  ✓ Generated: What is $\int x^4 dx = ?$
  ✓ Answer: $\frac{x^5}{5} + c$
  ✓ LaTeX valid: True

[2/15] Generating question for: U-Substitution Method
  ✓ Generated: Find $\int 2x(x^2 + 3)^4 dx$
  ✓ Answer: $\frac{(x^2+3)^5}{5} + c$
  ✓ LaTeX valid: True

✓ Generated 15 stems for this batch
✓ Total stems generated so far: 15

→ Loading next batch of 15 concepts
→ 15 concepts remaining in queue

============================================================
STEM GENERATOR NODE
============================================================
Processing batch of 15 concepts
[... continues for each batch ...]

✓ All concepts processed! Total stems: 45

============================================================
VALIDATOR NODE (SymPy validation disabled)
============================================================
Validating 45 generated questions

[1/45] Processing: What is $\int x^4 dx = ?$
  ✓ LaTeX valid - accepting question

============================================================
✓ Validated: 45
✗ Failed: 0
Success rate: 100.0%

============================================================
DISTRACTOR GENERATOR NODE
============================================================
Generating distractors for 45 questions

[1/45] Generating distractors for Q1
  Question: What is $\int x^4 dx = ?$
  ✓ Generated 5 distractors
  ✓ Selected top 3 distractors:
    1. $\frac{x^5}{4} + c$ (coefficient_error, score: 0.85)
    2. $4x^3 + c$ (derivative_instead, score: 0.78)
    3. $x^5 + c$ (coefficient_error, score: 0.72)

============================================================
DISTRACTOR GENERATION SUMMARY
============================================================
✓ Questions with distractors: 45
✓ Total distractors generated: 135
✓ Average per question: 3.0

============================================================
MCQ ASSEMBLY NODE
============================================================
Assembling 45 complete MCQs

[1/45] Assembling MCQ 1
  ✓ Assembled with options: a, b, c, d
  ✓ Correct answer: (b)

============================================================
ASSEMBLY SUMMARY
============================================================
✓ Total MCQs assembled: 45
✓ Difficulty distribution:
  - easy: 15 (33.3%)
  - medium: 25 (55.6%)
  - hard: 5 (11.1%)

✓ Exported 45 MCQs to: generated_mcqs.md

============================================================
FINAL METRICS
============================================================
total_concepts_extracted: 45
stems_generated: 45
questions_validated: 45
questions_failed: 0
validation_rate: 1.0
questions_with_distractors: 45
total_distractors_generated: 135
final_mcqs_count: 45
difficulty_distribution: {'easy': 15, 'medium': 25, 'hard': 5}

✓ Successfully generated 45 MCQs!
✓ Output saved to: generated_mcqs.md
```

---

## 🎯 **KEY TAKEAWAYS**

### **Input Requirements:**
- Chapter content: Markdown with formulas, examples, explanations
- Existing MCQs: Markdown with questions and options
- Should contain 30-50 concepts for optimal batch processing

### **Output Features:**
- 4 options per question (a, b, c, d)
- Correct answer in **bold**
- Comprehensive explanations for all options
- LaTeX formatting for mathematical expressions
- Metadata: difficulty, validation scores, integral types

### **Processing Pipeline:**
1. **Extract** → 30-50 concepts as structured JSON
2. **Generate** → Questions + correct answers (batches of 10-15)
3. **Validate** → LaTeX syntax checking (SymPy disabled)
4. **Distract** → 5 wrong answers → top 3 selected
5. **Assemble** → Shuffle, format, export markdown

### **Quality Controls:**
- Cognitive error taxonomy ensures pedagogically sound distractors
- Batch processing prevents LLM hallucination
- LaTeX validation ensures proper rendering
- Plausibility scoring ranks distractor quality
