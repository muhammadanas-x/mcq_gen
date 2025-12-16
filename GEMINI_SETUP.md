# Setup Guide for Google Gemini API

## Getting Your Gemini API Key

1. **Visit Google AI Studio**:
   - Go to https://aistudio.google.com/app/apikey
   - Sign in with your Google account

2. **Create API Key**:
   - Click "Create API Key"
   - Select a Google Cloud project (or create new one)
   - Copy your API key

3. **Add to .env file**:
   ```bash
   cp .env.example .env
   # Edit .env and add:
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

## Install Gemini Support

```bash
pip install -r requirements.txt
```

This installs `langchain-google-genai` for Gemini integration.

## Available Gemini Models

- **gemini-2.5-pro** (default): Fast, experimental, great for prototyping
- **gemini-1.5-pro**: More capable, better for complex reasoning
- **gemini-1.5-flash**: Fast and efficient

## Usage Examples

### Basic Usage
```bash
python main.py \
  --input ../chapter3.md \
  --input-type chapter \
  --output generated_mcqs.md \
  --llm gemini \
  --model gemini-2.5-pro
```

### Programmatic Usage
```python
from main import MCQGenerator

generator = MCQGenerator(
    llm_provider="gemini",
    model="gemini-2.5-pro",
    batch_size=15
)

mcqs = generator.generate_from_file(
    input_path="../chapter3.md",
    input_type="chapter",
    output_path="output.md"
)
```

## Cost Comparison (as of Dec 2024)

- **Gemini 2.0 Flash**: FREE up to 15 RPM, then very low cost
- **Gemini 1.5 Pro**: ~$3.50/1M input tokens, $10.50/1M output
- **Claude 3.5 Sonnet**: ~$3/1M input tokens, $15/1M output  
- **GPT-4**: ~$10/1M input tokens, $30/1M output

**Winner for FYP**: Gemini 2.0 Flash is FREE and fast! 🎉

## Rate Limits

Free tier:
- 15 requests per minute
- 1500 requests per day
- 1 million tokens per minute

This is sufficient for generating 50-100 MCQs.

## Testing Your Setup

```bash
# Test components
python test_components.py

# Quick test with small batch
python main.py \
  --input ../chap3_fung_mcqs.md \
  --input-type mcqs \
  --output test_output.md \
  --llm gemini \
  --batch-size 5
```

## Troubleshooting

### "GOOGLE_API_KEY not found"
- Make sure `.env` file exists in the `mcq_generator/` directory
- Check that you've added `GOOGLE_API_KEY=...` (not `GEMINI_API_KEY`)
- The key should be from Google AI Studio, not Google Cloud Console

### Rate limit errors
- Free tier: 15 requests/minute
- Add delays between batches if needed
- Reduce batch size to 5-10 for slower generation

### Import errors
- Make sure you've installed updated requirements:
  ```bash
  pip install -r requirements.txt
  ```

## Why Gemini for FYP?

✅ **Cost-effective**: FREE tier perfect for development and testing  
✅ **Fast**: 2.0 Flash is optimized for speed  
✅ **Good at math**: Handles LaTeX and mathematical reasoning well  
✅ **No billing required**: Can use without credit card  
✅ **Simple setup**: Just get API key, no complex auth  

Perfect for a student FYP project! 🎓
