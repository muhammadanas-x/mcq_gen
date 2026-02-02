# Subject-Wise Organization Guide

This document explains how MCQs are organized by subject in the database and how to use subject-based filtering.

---

## Overview

All MCQs, sessions, and concepts are now organized by **subject**. This allows you to:
- Generate MCQs for different courses/topics separately
- Filter and query by subject
- Track statistics per subject
- Build subject-specific question banks

---

## Subject Field

The `subject` field is a **required** string parameter that categorizes your MCQs.

### Naming Conventions

We recommend using descriptive subject names:

**Good Examples:**
```
"Calculus - Differentiation"
"Calculus - Integration"
"Linear Algebra - Matrices"
"Linear Algebra - Vector Spaces"
"Physics - Mechanics"
"Physics - Thermodynamics"
"Data Structures - Trees"
"Data Structures - Graphs"
```

**Keep it Consistent:**
- Use the same subject name format across sessions
- Include both broad topic and specific subtopic
- Use " - " (space-dash-space) as separator
- Capitalize consistently

---

## Database Schema with Subject

### Collections Overview

All three collections include the `subject` field:

1. **mcq_sessions** - Generation session metadata
2. **mcqs** - Generated multiple choice questions
3. **concepts** - Extracted concepts from input

### Indexes Created

For optimal performance, the following indexes are created:

**mcq_sessions:**
- `session_id` (unique)
- `subject`
- `created_at`
- `(subject, created_at)` compound

**mcqs:**
- `session_id`
- `subject`
- `metadata.difficulty`
- `(subject, session_id)` compound
- `(subject, difficulty)` compound
- `created_at`

**concepts:**
- `session_id`
- `subject`
- `concept_id`
- `(subject, session_id)` compound

---

## API Usage Examples

### 1. Generate MCQs with Subject

```bash
curl -X POST "http://localhost:8000/generate-mcqs" \
  -F "file=@calculus_chapter3.md" \
  -F "subject=Calculus - Integration" \
  -F "input_type=chapter" \
  -F "include_explanations=true"
```

**Python:**
```python
import requests

url = "http://localhost:8000/generate-mcqs"

with open("calculus_chapter3.md", "rb") as f:
    files = {"file": ("calculus_chapter3.md", f, "text/markdown")}
    data = {
        "subject": "Calculus - Integration",
        "input_type": "chapter",
        "include_explanations": True
    }
    
    response = requests.post(url, files=files, data=data)
    result = response.json()
    
    print(f"Generated {result['total_mcqs_generated']} MCQs for {data['subject']}")
```

### 2. List All Subjects

```bash
curl "http://localhost:8000/subjects"
```

**Response:**
```json
{
  "total_subjects": 5,
  "subjects": [
    {
      "subject": "Calculus - Differentiation",
      "total_sessions": 12,
      "total_mcqs": 540
    },
    {
      "subject": "Calculus - Integration",
      "total_sessions": 8,
      "total_mcqs": 360
    },
    {
      "subject": "Linear Algebra - Matrices",
      "total_sessions": 15,
      "total_mcqs": 675
    }
  ]
}
```

### 3. Filter Sessions by Subject

```bash
curl "http://localhost:8000/sessions?subject=Calculus%20-%20Integration&limit=10"
```

**Python:**
```python
import requests

response = requests.get(
    "http://localhost:8000/sessions",
    params={
        "subject": "Calculus - Integration",
        "limit": 10
    }
)

sessions = response.json()
print(f"Found {sessions['total']} sessions for this subject")
```

### 4. Filter MCQs by Subject

```bash
curl "http://localhost:8000/mcqs?subject=Linear%20Algebra&difficulty=medium&limit=20"
```

**Python:**
```python
import requests

response = requests.get(
    "http://localhost:8000/mcqs",
    params={
        "subject": "Linear Algebra - Matrices",
        "difficulty": "medium",
        "limit": 20
    }
)

mcqs = response.json()
print(f"Found {mcqs['total']} medium difficulty MCQs")
```

### 5. Get All MCQs for Multiple Subjects

```python
import requests

subjects = [
    "Calculus - Differentiation",
    "Calculus - Integration",
    "Calculus - Limits"
]

all_mcqs = []

for subject in subjects:
    response = requests.get(
        "http://localhost:8000/mcqs",
        params={"subject": subject, "limit": 100}
    )
    mcqs = response.json()
    all_mcqs.extend(mcqs['mcqs'])
    print(f"{subject}: {mcqs['total']} MCQs")

print(f"\nTotal MCQs across all Calculus subjects: {len(all_mcqs)}")
```

---

## Common Use Cases

### Build a Subject-Specific Question Bank

```python
import requests
import json

def build_question_bank(subject: str, output_file: str):
    """Download all MCQs for a subject and save to file"""
    
    all_mcqs = []
    skip = 0
    limit = 100
    
    while True:
        response = requests.get(
            "http://localhost:8000/mcqs",
            params={"subject": subject, "skip": skip, "limit": limit}
        )
        data = response.json()
        
        all_mcqs.extend(data['mcqs'])
        
        if len(data['mcqs']) < limit:
            break
        
        skip += limit
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump({
            "subject": subject,
            "total_mcqs": len(all_mcqs),
            "mcqs": all_mcqs
        }, f, indent=2)
    
    print(f"Saved {len(all_mcqs)} MCQs to {output_file}")

# Usage
build_question_bank("Calculus - Integration", "calculus_integration_bank.json")
```

### Generate Statistics by Subject

```python
import requests
from collections import defaultdict

def get_subject_statistics():
    """Get detailed statistics for all subjects"""
    
    response = requests.get("http://localhost:8000/subjects")
    subjects_data = response.json()
    
    for subject_stat in subjects_data['subjects']:
        subject = subject_stat['subject']
        
        # Get difficulty distribution
        response = requests.get(
            "http://localhost:8000/mcqs",
            params={"subject": subject, "limit": 1000}
        )
        mcqs = response.json()['mcqs']
        
        difficulty_count = defaultdict(int)
        for mcq in mcqs:
            difficulty_count[mcq['metadata']['difficulty']] += 1
        
        print(f"\n{subject}:")
        print(f"  Total Sessions: {subject_stat['total_sessions']}")
        print(f"  Total MCQs: {subject_stat['total_mcqs']}")
        print(f"  Difficulty Distribution:")
        print(f"    Easy: {difficulty_count['easy']}")
        print(f"    Medium: {difficulty_count['medium']}")
        print(f"    Hard: {difficulty_count['hard']}")

get_subject_statistics()
```

### Create Custom Exam by Subject

```python
import requests
import random

def create_custom_exam(subject: str, num_questions: int, difficulty_mix: dict):
    """
    Create a custom exam with specific difficulty distribution
    
    Args:
        subject: Subject name
        num_questions: Total questions in exam
        difficulty_mix: {"easy": 0.4, "medium": 0.4, "hard": 0.2}
    """
    
    exam_questions = []
    
    for difficulty, proportion in difficulty_mix.items():
        count = int(num_questions * proportion)
        
        response = requests.get(
            "http://localhost:8000/mcqs",
            params={
                "subject": subject,
                "difficulty": difficulty,
                "limit": count * 2  # Get more to allow random selection
            }
        )
        
        mcqs = response.json()['mcqs']
        selected = random.sample(mcqs, min(count, len(mcqs)))
        exam_questions.extend(selected)
    
    # Shuffle questions
    random.shuffle(exam_questions)
    
    print(f"Created exam for {subject} with {len(exam_questions)} questions")
    return exam_questions

# Create a balanced exam
exam = create_custom_exam(
    subject="Linear Algebra - Matrices",
    num_questions=30,
    difficulty_mix={"easy": 0.4, "medium": 0.4, "hard": 0.2}
)
```

---

## Database Queries (Direct MongoDB)

If you need to query the database directly:

### Find All Sessions for a Subject

```javascript
db.mcq_sessions.find({ "subject": "Calculus - Integration" })
  .sort({ "created_at": -1 })
```

### Count MCQs by Difficulty for a Subject

```javascript
db.mcqs.aggregate([
  { $match: { "subject": "Linear Algebra - Matrices" } },
  { $group: { 
      _id: "$metadata.difficulty", 
      count: { $sum: 1 } 
    }
  }
])
```

### Get All Subjects with Stats

```javascript
db.mcq_sessions.aggregate([
  { $group: {
      _id: "$subject",
      total_sessions: { $sum: 1 },
      latest_session: { $max: "$created_at" }
    }
  },
  { $sort: { "_id": 1 } }
])
```

### Find MCQs from Multiple Subjects

```javascript
db.mcqs.find({
  "subject": { 
    $in: [
      "Calculus - Differentiation",
      "Calculus - Integration"
    ]
  }
})
```

---

## Setup Instructions

### 1. Create Database Indexes

Run this script once to create all necessary indexes:

```bash
python create_indexes.py
```

This will create optimized indexes on the `subject` field in all collections.

### 2. Verify Indexes

Check that indexes were created:

```python
import asyncio
from database import get_async_database, COLLECTIONS

async def verify_indexes():
    db = await get_async_database()
    
    for collection_name in COLLECTIONS.values():
        indexes = await db[collection_name].index_information()
        print(f"\n{collection_name}:")
        for name, info in indexes.items():
            print(f"  {name}: {info['key']}")

asyncio.run(verify_indexes())
```

---

## Migration from Old Data (Without Subject)

If you have existing data without the `subject` field:

```python
import asyncio
from database import get_sync_database, COLLECTIONS

def migrate_add_subjects():
    """Add default subject to existing documents"""
    
    db = get_sync_database()
    default_subject = "Uncategorized"
    
    # Update sessions
    result = db[COLLECTIONS["mcq_sessions"]].update_many(
        {"subject": {"$exists": False}},
        {"$set": {"subject": default_subject}}
    )
    print(f"Updated {result.modified_count} sessions")
    
    # Update MCQs
    result = db[COLLECTIONS["mcqs"]].update_many(
        {"subject": {"$exists": False}},
        {"$set": {"subject": default_subject}}
    )
    print(f"Updated {result.modified_count} MCQs")
    
    # Update concepts
    result = db[COLLECTIONS["concepts"]].update_many(
        {"subject": {"$exists": False}},
        {"$set": {"subject": default_subject}}
    )
    print(f"Updated {result.modified_count} concepts")

migrate_add_subjects()
```

---

## Best Practices

1. **Consistent Naming**: Use the same subject name format across all generations
2. **Hierarchical Structure**: Use "Category - Subcategory" format
3. **Create Indexes**: Run `create_indexes.py` before heavy usage
4. **Monitor Growth**: Use `/subjects` endpoint to track database growth
5. **Regular Backups**: Back up MongoDB regularly, especially per subject
6. **Query Optimization**: Always filter by subject when possible for faster queries

---

## API Endpoints Summary

| Endpoint | Method | Subject Support | Description |
|----------|--------|-----------------|-------------|
| `/generate-mcqs` | POST | Required parameter | Generate MCQs with subject |
| `/subjects` | GET | - | List all subjects with stats |
| `/sessions` | GET | Optional filter | List sessions (filter by subject) |
| `/sessions/{id}` | GET | Returns subject | Get specific session |
| `/mcqs` | GET | Optional filter | List MCQs (filter by subject/difficulty) |
| `/mcqs/{id}` | GET | Returns subject | Get specific MCQ |

---

## Complete Example Workflow

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Step 1: Generate MCQs for a subject
with open("linear_algebra_matrices.md", "rb") as f:
    files = {"file": f}
    data = {"subject": "Linear Algebra - Matrices", "input_type": "chapter"}
    
    response = requests.post(f"{BASE_URL}/generate-mcqs", files=files, data=data)
    result = response.json()
    session_id = result['session_id']
    print(f"Generated {result['total_mcqs_generated']} MCQs")

# Step 2: List all subjects
response = requests.get(f"{BASE_URL}/subjects")
subjects = response.json()
print(f"\nTotal subjects in database: {subjects['total_subjects']}")

# Step 3: Get all MCQs for this subject
response = requests.get(
    f"{BASE_URL}/mcqs",
    params={"subject": "Linear Algebra - Matrices", "limit": 100}
)
mcqs = response.json()
print(f"Total MCQs for Linear Algebra - Matrices: {mcqs['total']}")

# Step 4: Get medium difficulty MCQs
response = requests.get(
    f"{BASE_URL}/mcqs",
    params={
        "subject": "Linear Algebra - Matrices",
        "difficulty": "medium",
        "limit": 50
    }
)
medium_mcqs = response.json()
print(f"Medium difficulty MCQs: {medium_mcqs['total']}")

# Step 5: Save subject-specific question bank
with open("linear_algebra_matrices_bank.json", "w") as f:
    json.dump(mcqs, f, indent=2)
print("Saved question bank to file")
```

---

## Troubleshooting

### Subject Not Found in Old Sessions

If you query by subject and get no results for old data:
- Run the migration script above
- Or manually update documents in MongoDB

### Slow Queries

If queries are slow:
- Ensure indexes are created (`python create_indexes.py`)
- Verify indexes exist using MongoDB Compass or shell
- Consider adding more specific compound indexes

### Inconsistent Subject Names

If you have variations like "Calculus Integration" vs "Calculus - Integration":
- Standardize naming going forward
- Use MongoDB aggregation to find variations
- Run update scripts to normalize existing data

---

## Summary

The subject-wise organization provides:
- ✅ Organized question banks by topic
- ✅ Fast filtering and queries
- ✅ Subject-level statistics
- ✅ Flexible exam creation
- ✅ Scalable database structure
- ✅ Easy backup and export per subject

Start using subjects in your MCQ generation to build organized, searchable question banks!
