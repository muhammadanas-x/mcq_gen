# 🚀 Quick Reference - MCQ Generator API

## One-Time Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env:
#   - Add MongoDB Atlas URI
#   - Add LLM API key (Gemini/Claude/OpenAI)

# 3. Start server
python start_server.py
```

---

## API Endpoints

### Generate MCQs
```bash
curl -X POST "http://localhost:8000/generate-mcqs" \
  -F "file=@chapter3.md" \
  -F "input_type=chapter" \
  -F "include_explanations=true"
```

### Health Check
```bash
curl http://localhost:8000/health
```

### List Sessions
```bash
curl http://localhost:8000/sessions
```

### List MCQs
```bash
curl "http://localhost:8000/mcqs?session_id=YOUR_SESSION_ID"
```

---

## Access Points

| Resource | URL |
|----------|-----|
| API Server | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

---

## Environment Variables (.env)

```env
# MongoDB (Required)
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DB_NAME=mcq_generator

# LLM API Key (Choose one)
GOOGLE_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here

# Defaults
DEFAULT_LLM_PROVIDER=gemini
DEFAULT_MODEL=gemini-2.5-pro
DEFAULT_BATCH_SIZE=15
```

---

## Python Client Example

```python
import requests

# Generate MCQs
with open("chapter3.md", "rb") as f:
    response = requests.post(
        "http://localhost:8000/generate-mcqs",
        files={"file": f},
        data={"input_type": "chapter"}
    )

result = response.json()
print(f"Session ID: {result['session_id']}")
print(f"MCQs Generated: {result['total_mcqs_generated']}")

# Get all MCQs from session
mcqs = requests.get(
    f"http://localhost:8000/mcqs",
    params={"session_id": result['session_id']}
).json()

for mcq in mcqs['mcqs']:
    print(f"Q{mcq['question_number']}: {mcq['stem']}")
```

---

## Testing

```bash
# Run test suite
python test_api.py

# Test individual endpoint
curl http://localhost:8000/health
```

---

## MongoDB Collections

| Collection | Contains |
|------------|----------|
| mcq_sessions | Session metadata |
| mcqs | Individual MCQs |
| concepts | Extracted concepts |

---

## File Structure

```
mcq_gen/
├── server.py              # FastAPI application
├── database.py            # MongoDB connection
├── models.py              # Pydantic models
├── storage.py             # Storage service
├── start_server.py        # Server startup
├── test_api.py            # API tests
│
├── API_README.md          # API documentation
├── SETUP_GUIDE.md         # Setup instructions
├── CONVERSION_SUMMARY.md  # Implementation notes
│
└── [Original files unchanged]
    ├── main.py            # CLI (still works)
    ├── graph.py           # LangGraph
    ├── state.py           # State schema
    └── nodes/             # Processing nodes
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Database connection failed | Check MongoDB URI in .env |
| API key error | Verify LLM API key is set |
| Module not found | Run `pip install -r requirements.txt` |
| Port already in use | Change port in server.py or kill process |

---

## Documentation

- **Full API Docs**: [API_README.md](API_README.md)
- **Setup Guide**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Examples**: [INPUT_OUTPUT_EXAMPLES.md](INPUT_OUTPUT_EXAMPLES.md)
- **Interactive**: http://localhost:8000/docs

---

## Default Configuration

- **LLM Provider**: Gemini
- **Model**: gemini-2.5-pro
- **Batch Size**: 15 concepts
- **Port**: 8000
- **Host**: 0.0.0.0 (all interfaces)

Override via form fields in API requests.

---

## Key Features

✅ Synchronous processing  
✅ File upload via multipart form-data  
✅ MongoDB Atlas storage  
✅ No authentication  
✅ Environment-based defaults  
✅ Original logic unchanged  
✅ Full CRUD operations  
✅ Interactive API docs  

---

**Need help? Check [SETUP_GUIDE.md](SETUP_GUIDE.md) or [API_README.md](API_README.md)**
