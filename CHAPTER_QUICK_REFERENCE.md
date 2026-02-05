# Quick Reference - Chapter Organization

## ⚡ Quick Start

### Generate MCQs (NEW - chapter required)
```bash
curl -X POST "http://localhost:8000/generate-mcqs" \
  -F "file=@chapter3.md" \
  -F "subject=Calculus" \
  -F "chapter=Chapter 3 - Definite Integrals"
```

### Query MCQs by Subject + Chapter
```bash
# All Calculus
GET /mcqs?subject=Calculus

# Specific Chapter
GET /mcqs?subject=Calculus&chapter=Chapter%203%20-%20Definite%20Integrals

# Chapter + Difficulty
GET /mcqs?subject=Calculus&chapter=Chapter%203&difficulty=medium
```

---

## 📊 Database Organization

```
Subject (e.g., "Calculus")
  └── Chapter (e.g., "Chapter 3 - Definite Integrals")
        └── Questions (42 MCQs)
```

---

## 🔧 What Changed

| Component | Change | Status |
|-----------|--------|--------|
| `POST /generate-mcqs` | Added `chapter` parameter | ✅ REQUIRED |
| `GET /sessions` | Added `?chapter=...` filter | ✅ Optional |
| `GET /mcqs` | Added `?chapter=...` filter | ✅ Optional |
| Database Schema | Added `chapter` field | ✅ All collections |
| Indexes | Added `chapter` + `(subject,chapter)` | ✅ All collections |

---

## 📝 Migration (One-Time)

If you have existing data:

```bash
python update_database_indexes.py
```

This adds "Unknown Chapter" to old records and creates new indexes.

---

## 💡 Best Practices

### Subject Names
- ✅ "Calculus"
- ✅ "Linear Algebra"
- ❌ "Calculus - Integration" (too specific)

### Chapter Names
- ✅ "Chapter 3 - Definite Integrals"
- ✅ "Unit 2 - Matrix Operations"
- ❌ "Integration" (missing number)

---

## 📖 Documentation

- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Full database schema
- [CHAPTER_ORGANIZATION_GUIDE.md](CHAPTER_ORGANIZATION_GUIDE.md) - Complete guide
- [CHAPTER_IMPLEMENTATION_SUMMARY.md](CHAPTER_IMPLEMENTATION_SUMMARY.md) - Implementation details
