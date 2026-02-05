# Chapter Organization Guide

## Overview

The MCQ Generator now supports **hierarchical organization** of questions by **Subject** and **Chapter**. This allows you to organize and retrieve MCQs at different levels of granularity.

---

## Hierarchy Structure

```
Subject (e.g., "Calculus")
  └── Chapter (e.g., "Chapter 3 - Definite Integrals")
        └── Questions/MCQs
```

---

## API Usage

### Generating MCQs with Chapter

When generating MCQs, you must provide both `subject` and `chapter`:

```bash
curl -X POST "http://localhost:8000/generate-mcqs" \
  -F "file=@chapter3.md" \
  -F "subject=Calculus" \
  -F "chapter=Chapter 3 - Definite Integrals" \
  -F "input_type=chapter"
```

**Form Fields:**
- `file`: Markdown file containing chapter content
- `subject`: Subject name (e.g., "Calculus", "Linear Algebra")
- `chapter`: Chapter name (e.g., "Chapter 3 - Definite Integrals")
- `input_type`: "chapter" or "mcqs"
- `include_explanations`: true/false (default: true)

---

## Filtering by Subject and Chapter

### 1. List Sessions

**Filter by subject only:**
```bash
GET /sessions?subject=Calculus
```

**Filter by subject and chapter:**
```bash
GET /sessions?subject=Calculus&chapter=Chapter%203%20-%20Definite%20Integrals
```

**Response:**
```json
{
  "total": 2,
  "sessions": [
    {
      "id": "...",
      "session_id": "...",
      "subject": "Calculus",
      "chapter": "Chapter 3 - Definite Integrals",
      "total_mcqs_generated": 42,
      "status": "completed",
      ...
    }
  ]
}
```

### 2. List MCQs

**Filter by subject only:**
```bash
GET /mcqs?subject=Calculus
```

**Filter by subject and chapter:**
```bash
GET /mcqs?subject=Calculus&chapter=Chapter%203%20-%20Definite%20Integrals
```

**Filter by subject, chapter, and difficulty:**
```bash
GET /mcqs?subject=Calculus&chapter=Chapter%203%20-%20Definite%20Integrals&difficulty=medium
```

**Response:**
```json
{
  "total": 42,
  "mcqs": [
    {
      "id": "...",
      "session_id": "...",
      "subject": "Calculus",
      "chapter": "Chapter 3 - Definite Integrals",
      "question_number": 1,
      "stem": "Find $\\int_0^1 x^2 dx$",
      ...
    }
  ]
}
```

---

## Database Organization

All three collections store `subject` and `chapter` fields:

### mcq_sessions
- Each session belongs to a specific subject and chapter
- Indexed on: `subject`, `chapter`, and `(subject, chapter)` compound

### mcqs
- Each MCQ belongs to a specific subject and chapter
- Indexed on: `subject`, `chapter`, and `(subject, chapter)` compound

### concepts
- Each concept belongs to a specific subject and chapter
- Indexed on: `subject`, `chapter`, and `(subject, chapter)` compound

---

## MongoDB Queries

### Get all chapters for a subject
```javascript
db.mcq_sessions.distinct("chapter", { subject: "Calculus" })
```

### Get MCQ count by chapter
```javascript
db.mcqs.aggregate([
  { $match: { subject: "Calculus" } },
  { $group: { _id: "$chapter", count: { $sum: 1 } } },
  { $sort: { _id: 1 } }
])
```

### Get difficulty distribution for a specific chapter
```javascript
db.mcqs.aggregate([
  { 
    $match: { 
      subject: "Calculus",
      chapter: "Chapter 3 - Definite Integrals"
    }
  },
  { $group: { _id: "$metadata.difficulty", count: { $sum: 1 } } }
])
```

---

## Naming Conventions

### Subject Names
- Keep subjects concise and consistent
- Examples:
  - ✅ "Calculus"
  - ✅ "Linear Algebra"
  - ✅ "Probability and Statistics"
  - ❌ "Calculus - Integration Techniques" (too specific, use chapter field)

### Chapter Names
- Include chapter number and descriptive title
- Examples:
  - ✅ "Chapter 1 - Limits and Continuity"
  - ✅ "Chapter 3 - Definite Integrals"
  - ✅ "Unit 2 - Matrix Operations"
  - ❌ "Integration" (missing chapter number)
  - ❌ "Ch3" (not descriptive enough)

---

## Example Workflow

### 1. Generate MCQs for Multiple Chapters

**Chapter 1:**
```bash
curl -X POST "http://localhost:8000/generate-mcqs" \
  -F "file=@chapter1.md" \
  -F "subject=Calculus" \
  -F "chapter=Chapter 1 - Limits and Continuity"
```

**Chapter 2:**
```bash
curl -X POST "http://localhost:8000/generate-mcqs" \
  -F "file=@chapter2.md" \
  -F "subject=Calculus" \
  -F "chapter=Chapter 2 - Derivatives"
```

**Chapter 3:**
```bash
curl -X POST "http://localhost:8000/generate-mcqs" \
  -F "file=@chapter3.md" \
  -F "subject=Calculus" \
  -F "chapter=Chapter 3 - Definite Integrals"
```

### 2. Retrieve All Calculus Questions
```bash
GET /mcqs?subject=Calculus&limit=100
```

### 3. Retrieve Only Chapter 3 Questions
```bash
GET /mcqs?subject=Calculus&chapter=Chapter%203%20-%20Definite%20Integrals&limit=50
```

### 4. Get Medium Difficulty Questions from Chapter 3
```bash
GET /mcqs?subject=Calculus&chapter=Chapter%203%20-%20Definite%20Integrals&difficulty=medium
```

---

## Migration from Old Schema

If you have existing data without chapter field, run:

```bash
python update_database_indexes.py
```

This will:
1. Add default "Unknown Chapter" to existing documents
2. Create new indexes for chapter field
3. Create compound indexes for (subject, chapter)

---

## Benefits

1. **Hierarchical Organization**: Organize questions by subject → chapter
2. **Flexible Filtering**: Filter at subject level or drill down to specific chapters
3. **Scalability**: Efficiently handle hundreds of chapters per subject
4. **Clear Structure**: Mirror textbook organization in database
5. **Performance**: Compound indexes optimize hierarchical queries
