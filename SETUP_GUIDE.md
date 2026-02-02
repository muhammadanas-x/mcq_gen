# Complete Setup Guide - MCQ Generator API

Step-by-step guide to set up and run the MCQ Generator FastAPI server with MongoDB Atlas.

---

## 📋 Prerequisites

- Python 3.8+ installed
- MongoDB Atlas account (free tier works)
- LLM API key (Google Gemini, Anthropic Claude, or OpenAI)

---

## 🚀 Step-by-Step Setup

### Step 1: Clone/Download Repository

```bash
cd mcq_gen
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI & Uvicorn (API server)
- Motor & PyMongo (MongoDB async/sync drivers)
- LangChain & LangGraph (MCQ generation)
- LLM provider packages (Gemini, Anthropic, OpenAI)
- SymPy, PyLatexEnc (mathematical processing)

### Step 3: Set Up MongoDB Atlas

#### 3.1 Create MongoDB Atlas Account

1. Go to https://www.mongodb.com/cloud/atlas/register
2. Sign up for free account
3. Create a free M0 cluster (512MB storage, perfect for this project)

#### 3.2 Configure Database Access

1. In MongoDB Atlas dashboard, go to **Database Access**
2. Click **Add New Database User**
3. Create user with username/password
4. Grant **Read and write to any database** role

#### 3.3 Configure Network Access

1. Go to **Network Access**
2. Click **Add IP Address**
3. For testing: Click **Allow Access from Anywhere** (0.0.0.0/0)
4. For production: Add your server's specific IP address

#### 3.4 Get Connection String

1. Go to **Databases** → Click **Connect** on your cluster
2. Choose **Connect your application**
3. Copy the connection string, it looks like:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
4. Replace `<username>` and `<password>` with your database user credentials

### Step 4: Get LLM API Key

Choose ONE provider (or configure multiple):

#### Option A: Google Gemini (Recommended - Free tier available)

1. Go to https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Click **Create API Key**
4. Copy the API key

#### Option B: Anthropic Claude

1. Go to https://console.anthropic.com/
2. Sign up/login
3. Go to **API Keys**
4. Create new key
5. Copy the API key

#### Option C: OpenAI

1. Go to https://platform.openai.com/api-keys
2. Sign up/login
3. Create new secret key
4. Copy the API key

### Step 5: Configure Environment Variables

1. Copy example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` file with your credentials:

   ```env
   # MongoDB Atlas
   MONGODB_URI=mongodb+srv://youruser:yourpassword@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   MONGODB_DB_NAME=mcq_generator

   # LLM API Key (choose one or more)
   GOOGLE_API_KEY=your_actual_google_api_key_here
   # ANTHROPIC_API_KEY=your_actual_anthropic_api_key_here
   # OPENAI_API_KEY=your_actual_openai_api_key_here

   # Default Configuration
   DEFAULT_LLM_PROVIDER=gemini
   DEFAULT_MODEL=gemini-2.5-pro
   DEFAULT_BATCH_SIZE=15
   ```

3. **Important**: Replace placeholder values with your actual credentials

### Step 6: Start the Server

Run the startup script (includes health checks):

```bash
python start_server.py
```

Or start directly with uvicorn:

```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

You should see:

```
✓ FastAPI server started
✓ MongoDB connection initialized
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 7: Verify Installation

#### 7.1 Test API Health

Open browser and go to: http://localhost:8000/health

You should see:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-02-02T10:30:00.000Z"
}
```

#### 7.2 Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Step 8: Test MCQ Generation

#### 8.1 Using the Interactive Swagger UI

1. Go to http://localhost:8000/docs
2. Click on `POST /generate-mcqs`
3. Click **Try it out**
4. Upload a markdown file (chapter content or existing MCQs)
5. Set parameters:
   - `input_type`: chapter or mcqs
   - `include_explanations`: true
6. Click **Execute**
7. Wait for completion (2-5 minutes)
8. Check response with generated MCQs

#### 8.2 Using cURL

```bash
curl -X POST "http://localhost:8000/generate-mcqs" \
  -F "file=@chapter3.md" \
  -F "input_type=chapter" \
  -F "include_explanations=true"
```

#### 8.3 Using Python Test Script

```bash
python test_api.py
```

This runs a comprehensive test suite.

---

## 📊 Verify Database

1. Go to MongoDB Atlas dashboard
2. Click **Browse Collections** on your cluster
3. Select database: `mcq_generator`
4. You should see three collections:
   - `mcq_sessions` - Generation session metadata
   - `mcqs` - Individual MCQ documents
   - `concepts` - Extracted concepts

---

## 🔍 Troubleshooting

### Problem: "Database connection failed"

**Solutions:**
1. Verify MongoDB URI in `.env` is correct
2. Check username/password are properly URL-encoded
3. Verify IP address is whitelisted in MongoDB Atlas
4. Test connection with MongoDB Compass or mongosh

### Problem: "LLM API key error"

**Solutions:**
1. Verify API key in `.env` is correct
2. Check you've set the right provider (GOOGLE_API_KEY, ANTHROPIC_API_KEY, etc.)
3. Verify API key has sufficient quota/credits
4. Check DEFAULT_LLM_PROVIDER matches your configured key

### Problem: "Module not found"

**Solutions:**
1. Make sure you installed dependencies: `pip install -r requirements.txt`
2. Check you're in the correct virtual environment
3. Try reinstalling: `pip install --upgrade -r requirements.txt`

### Problem: "File upload fails"

**Solutions:**
1. Ensure file is `.md` (markdown) format
2. Check file size is reasonable (< 10MB)
3. Verify file encoding is UTF-8
4. Try with a simpler test file first

### Problem: "Generation takes too long"

**Solutions:**
1. Reduce batch size (try 5-10 instead of 15)
2. Use a faster model (gemini-2.0-flash instead of gemini-2.5-pro)
3. Provide smaller input files (extract specific sections)
4. Check LLM API response times

---

## 🎯 Next Steps

1. **Generate your first MCQs**: Use the API with your own content
2. **Query the database**: Retrieve MCQs using GET endpoints
3. **Integrate with frontend**: Build a UI that calls these APIs
4. **Customize prompts**: Modify node files to adjust generation style
5. **Add features**: Extend the API with additional endpoints

---

## 📚 Additional Resources

- **API Documentation**: See [API_README.md](API_README.md)
- **Input/Output Examples**: See [INPUT_OUTPUT_EXAMPLES.md](INPUT_OUTPUT_EXAMPLES.md)
- **Implementation Guide**: See [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)
- **MongoDB Docs**: https://www.mongodb.com/docs/atlas/
- **FastAPI Docs**: https://fastapi.tiangolo.com/

---

## 🔐 Security Notes

For production deployment:

1. **Never commit `.env` file** (already in .gitignore)
2. **Use environment variables** or secrets manager in production
3. **Restrict MongoDB IP whitelist** to specific server IPs
4. **Add API authentication** (JWT tokens, API keys)
5. **Use HTTPS** with proper SSL certificates
6. **Configure CORS** appropriately for your domain
7. **Rate limit** API endpoints to prevent abuse

---

## ✅ Checklist

- [ ] Python 3.8+ installed
- [ ] MongoDB Atlas account created
- [ ] Database user created with credentials
- [ ] IP address whitelisted
- [ ] Connection string obtained
- [ ] LLM API key obtained (Gemini/Claude/OpenAI)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created and configured
- [ ] Server starts successfully
- [ ] Health check returns "healthy"
- [ ] Can access Swagger UI at /docs
- [ ] Successfully generated first MCQs
- [ ] Data appears in MongoDB Atlas collections

---

**Congratulations! Your MCQ Generator API is ready to use! 🎉**
