# MCQ Generator - FastAPI Server

A REST API for generating high-quality multiple-choice questions for calculus/integration topics with MongoDB Atlas storage.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your credentials:
# - MongoDB Atlas connection string
# - LLM API key (Gemini, Anthropic, or OpenAI)
```

**Required Environment Variables:**

```env
# MongoDB Atlas
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=mcq_generator

# LLM API Key (choose one)
GOOGLE_API_KEY=your_google_gemini_api_key_here
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# OPENAI_API_KEY=your_openai_api_key_here

# Defaults
DEFAULT_LLM_PROVIDER=gemini
DEFAULT_MODEL=gemini-2.5-pro
DEFAULT_BATCH_SIZE=15
```

### 3. Start the Server

```bash
python server.py
```

Or with uvicorn directly:

```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

Server will start at: **http://localhost:8000**

### 4. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📋 API Endpoints

### **Root**

```http
GET /
```

Returns API information and available endpoints.

---

### **Health Check**

```http
GET /health
```

Checks API and database connectivity.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-02-02T10:30:00.000Z"
}
```

---

### **Generate MCQs**

```http
POST /generate-mcqs
```

**Content-Type:** `multipart/form-data`

**Form Fields:**
- `file` (required): Markdown file (chapter content or existing MCQs)
- `subject` (required): Subject name (e.g., `"Calculus - Integration"`, `"Linear Algebra"`)
- `input_type` (optional): `"chapter"` or `"mcqs"` (default: `"chapter"`)
- `include_explanations` (optional): `true` or `false` (default: `true`)
- `llm_provider` (optional): `"gemini"`, `"anthropic"`, or `"openai"` (uses env default)
- `model` (optional): Model name (uses env default)
- `batch_size` (optional): Batch size for processing (uses env default)

**Example with cURL:**

```bash
curl -X POST "http://localhost:8000/generate-mcqs" \
  -F "file=@chapter3.md" \
  -F "subject=Calculus - Integration" \
  -F "input_type=chapter" \
  -F "include_explanations=true"
```

**Example with Python:**

```python
import requests

url = "http://localhost:8000/generate-mcqs"

with open("chapter3.md", "rb") as f:
    files = {"file": ("chapter3.md", f, "text/markdown")}
    data = {
        "subject": "Calculus - Integration",
        "input_type": "chapter",
        "include_explanations": True
    }
    
    response = requests.post(url, files=files, data=data)
    result = response.json()
    
    print(f"Session ID: {result['session_id']}")
    print(f"MCQs Generated: {result['total_mcqs_generated']}")
```

**Response:**

```json
{
  "session_id": "uuid-1234-5678-abcd",
  "message": "MCQs generated successfully",
  "total_mcqs_generated": 45,
  "difficulty_distribution": {
    "easy": 15,
    "medium": 25,
    "hard": 5
  },
  "metrics": {
    "total_concepts_extracted": 45,
    "total_mcqs_generated": 45,
    "validation_rate": 1.0
  },
  "mcqs": [
    {
      "id": "507f1f77bcf86cd799439011",
      "session_id": "uuid-1234-5678-abcd",
      "question_number": 1,
      "stem": "What is $\\int x^4 dx = ?$",
      "options": {
        "a": "$\\frac{x^5}{5} + c$",
        "b": "$4x^3 + c$",
        "c": "$x^5 + c$",
        "d": "$\\frac{x^5}{4} + c$"
      },
      "correct_answer": "a",
      "explanation": {
        "correct": "This is the correct answer...",
        "a": "...",
        "b": "...",
        "c": "...",
        "d": "..."
      },
      "metadata": {
        "difficulty": "easy",
        "validation_score": 1.0
      },
      "created_at": "2026-02-02T10:30:00.000Z"
    }
  ],
  "markdown_content": "### Generated MCQs: Integration\n..."
}
```

---

### **List Sessions**

```http
GET /sessions?subject=Calculus&skip=0&limit=10
```

Get all MCQ generation sessions (paginated). Optionally filter by subject.

**Query Parameters:**
- `subject` (optional): Filter by subject name
- `skip` (optional): Number to skip (default: 0)
- `limit` (optional): Maximum to return (default: 10, max: 100)

**Response:**

```json
{
  "total": 25,
  "sessions": [
    {
      "id": "507f1f77bcf86cd799439011",
      "session_id": "uuid-1234-5678-abcd",
      "subject": "Calculus - Integration",
      "input_filename": "chapter3.md",
      "input_type": "chapter",
      "llm_provider": "gemini",
      "model": "gemini-2.5-pro",
      "total_concepts_extracted": 45,
      "total_mcqs_generated": 45,
      "difficulty_distribution": {
        "easy": 15,
        "medium": 25,
        "hard": 5
      },
      "status": "completed",
      "created_at": "2026-02-02T10:30:00.000Z",
      "completed_at": "2026-02-02T10:35:00.000Z"
    }
  ]
}
```

---

### **Get Session Details**

```http
GET /sessions/{session_id}
```

Get details of a specific generation session.

---

### **List Subjects**

```http
GET /subjects
```

Get all unique subjects with statistics.

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
      "subject": "Linear Algebra",
      "total_sessions": 15,
      "total_mcqs": 675
    }
  ]
}
```

---

### **List MCQs**

```http
GET /mcqs?subject=Calculus&difficulty=medium&skip=0&limit=10
```

Get all generated MCQs (paginated). Filter by subject, session, and/or difficulty.

**Query Parameters:**
- `subject` (optional): Filter by subject name
- `session_id` (optional): Filter by session
- `difficulty` (optional): Filter by difficulty (easy, medium, hard)
- `skip` (optional): Number to skip (default: 0)
- `limit` (optional): Maximum to return (default: 10, max: 100)

---

### **Get MCQ Details**

```http
GET /mcqs/{mcq_id}
```

Get details of a specific MCQ.

---

## 🗄️ MongoDB Collections

The API stores data in three collections organized by subject:

### **mcq_sessions**
Stores generation session metadata:
- `session_id`: Unique session identifier
- `input_filename`: Name of uploaded file
- `input_type`: "chapter" or "mcqs"
- `llm_provider`, `model`, `batch_size`: Configuration used
- `total_concepts_extracted`, `total_mcqs_generated`: Metrics
- `difficulty_distribution`: Distribution of easy/medium/hard
- `status`: "processing", "completed", or "failed"
- `created_at`, `completed_at`: Timestamps

### **mcqs**
Stores individual MCQs:
- `session_id`: Reference to parent session
- `question_number`: Question number in sequence
- `concept_id`: Associated concept
- `stem`: Question text
- `options`: Map of a/b/c/d options
- `correct_answer`: Correct option key
- `explanation`: Explanations for all options
- `metadata`: Difficulty, validation scores, etc.
- `created_at`: Timestamp

### **concepts**
Stores extracted concepts:
- `concept_id`: Unique concept identifier
- `concept_name`: Human-readable name
- `formula`: LaTeX formula
- `difficulty`: "easy", "medium", or "hard"
- `prerequisites`: List of prerequisite concepts
- `context`: Explanation text
- `worked_example`: Optional example
- `session_id`: Reference to parent session
- `created_at`: Timestamp

---

## 🧪 Testing

### Test with cURL

```bash
# Health check
curl http://localhost:8000/health

# Generate MCQs
curl -X POST "http://localhost:8000/generate-mcqs" \
  -F "file=@chapter3.md" \
  -F "input_type=chapter"

# List sessions
curl http://localhost:8000/sessions

# List MCQs from specific session
curl "http://localhost:8000/mcqs?session_id=YOUR_SESSION_ID"
```

### Test with Python

See `test_api.py` for a complete example.

---

## 🔧 Configuration

### Default Settings

Default values are loaded from `.env`:

```env
DEFAULT_LLM_PROVIDER=gemini
DEFAULT_MODEL=gemini-2.5-pro
DEFAULT_BATCH_SIZE=15
```

These can be overridden per request via form fields.

### MongoDB Connection

Configure your MongoDB Atlas connection string in `.env`:

```env
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=mcq_generator
```

---

## 📊 Response Status Codes

- `200 OK`: Successful request
- `400 Bad Request`: Invalid input (wrong file type, invalid parameters)
- `404 Not Found`: Resource not found (session or MCQ ID)
- `500 Internal Server Error`: Generation failed
- `503 Service Unavailable`: Database connection failed

---

## 🚀 Production Deployment

For production deployment:

1. **Set proper CORS origins** in `server.py`:
   ```python
   allow_origins=["https://yourdomain.com"]
   ```

2. **Use production WSGI server**:
   ```bash
   pip install gunicorn
   gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

3. **Set up reverse proxy** (nginx, etc.)

4. **Configure MongoDB Atlas**:
   - Whitelist server IP
   - Use secure credentials
   - Enable monitoring

5. **Environment variables**: Use secrets management (not `.env` file)

---

## 📝 Notes

- **Synchronous Processing**: MCQ generation is synchronous - the API waits for completion before returning
- **File Cleanup**: Uploaded files are automatically deleted after processing
- **No Authentication**: Currently no authentication is implemented - add as needed
- **Inner Workings**: The existing MCQGenerator logic is completely unchanged - this is just a wrapper

---

## 🔍 Example Workflow

1. Upload chapter content
2. API generates MCQs (takes 2-5 minutes)
3. Returns session ID and all MCQs
4. Query database for MCQs anytime using session ID
5. Data persists in MongoDB Atlas

---

## 🐛 Troubleshooting

### Database Connection Failed

- Check MongoDB Atlas connection string
- Verify IP whitelist in MongoDB Atlas
- Test connection with `mongosh`

### LLM API Errors

- Verify API key in `.env`
- Check API quotas/limits
- Review error logs for details

### File Upload Issues

- Ensure file is `.md` format
- Check file size limits
- Verify multipart/form-data encoding

---

## 📚 Documentation

- **Swagger UI**: http://localhost:8000/docs - Interactive API testing
- **ReDoc**: http://localhost:8000/redoc - Clean documentation view
- **Original README**: See `README.md` for MCQ generator details
