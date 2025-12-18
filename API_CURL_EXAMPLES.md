# AI News Agent - API CURL Examples

This guide provides step-by-step curl commands to test all API endpoints of the AI News Agent application.

## Prerequisites

1. **Start the API server:**
   ```bash
   python3 main.py --mode api --host 0.0.0.0 --port 8000
   ```

2. **Ensure your `.env` file has:**
   ```
   LLM_MODEL_NAME=groq/mixtral-8x7b-32768
   TAVILY_API_KEY=your_key
   GROQ_API_KEY=your_key
   ```

3. **API Base URL:**
   ```
   http://localhost:8000
   ```

---

## 1. Health Check

### Check API Health Status

```bash
curl -X GET http://localhost:8000/health \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-18T14:30:00.123456",
  "version": "1.0.0",
  "llm_model": "groq/mixtral-8x7b-32768"
}
```

---

## 2. Generate Article (Direct - Synchronous)

### Generate a news article on a specific topic

```bash
curl -X POST http://localhost:8000/api/v1/articles/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Latest developments in Artificial Intelligence"
  }'
```

**Expected Response:**
```json
{
  "status": "completed",
  "topic": "Latest developments in Artificial Intelligence",
  "article": "📰 FINAL NEWS ARTICLE\n...[full article content]...",
  "research_summary": "Research findings from web search...",
  "references": [
    "https://example1.com",
    "https://example2.com"
  ],
  "created_at": "2024-12-18T14:30:00.123456",
  "completed_at": "2024-12-18T14:32:15.654321",
  "error": null,
  "markdown_content": "📰 FINAL NEWS ARTICLE\n...[full article content]..."
}
```

**Time:** Takes 2-3 minutes depending on API response times

---

## 3. Different Article Topics (Examples)

### Technology News
```bash
curl -X POST http://localhost:8000/api/v1/articles/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "OpenAI releases GPT-5 with breakthrough capabilities"
  }'
```

### Business News
```bash
curl -X POST http://localhost:8000/api/v1/articles/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Tech companies announce record quarterly earnings"
  }'
```

### Science News
```bash
curl -X POST http://localhost:8000/api/v1/articles/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Scientists discover new exoplanet with potential for life"
  }'
```

### Sports News
```bash
curl -X POST http://localhost:8000/api/v1/articles/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Major championship finals results and analysis"
  }'
```

---

## 4. List All Articles

### Get all completed articles (limit 10)

```bash
curl -X GET http://localhost:8000/api/v1/articles/list \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
[
  {
    "status": "completed",
    "topic": "Latest developments in Artificial Intelligence",
    "article": "📰 FINAL NEWS ARTICLE\n...",
    "research_summary": "...",
    "references": ["https://example.com"],
    "created_at": "2024-12-18T14:30:00.123456",
    "completed_at": "2024-12-18T14:32:15.654321",
    "error": null,
    "markdown_content": "..."
  }
]
```

### Filter by Status

```bash
curl -X GET "http://localhost:8000/api/v1/articles/list?status=completed&limit=5" \
  -H "Content-Type: application/json"
```

### Custom Limit

```bash
curl -X GET "http://localhost:8000/api/v1/articles/list?limit=20" \
  -H "Content-Type: application/json"
```

---

## 5. Get Statistics

### View system statistics

```bash
curl -X GET http://localhost:8000/api/v1/stats \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "total_jobs": 3,
  "status_breakdown": {
    "completed": 3,
    "pending": 0,
    "researching": 0,
    "writing": 0,
    "editing": 0,
    "saving": 0,
    "failed": 0
  },
  "timestamp": "2024-12-18T14:35:00.123456",
  "llm_model": "groq/mixtral-8x7b-32768"
}
```

---

## 6. Download Latest Article as Markdown

### Download the most recent article

```bash
curl -X GET http://localhost:8000/api/v1/articles/download-markdown \
  -H "Content-Type: application/json" \
  -o article.md
```

**Output:** Saves the markdown file as `article.md` in current directory

**Display in Terminal:**
```bash
curl -X GET http://localhost:8000/api/v1/articles/download-markdown \
  -H "Content-Type: application/json"
```

---

## 7. Complete Workflow Example

Run these commands in sequence to see the full workflow:

### Step 1: Check API is running
```bash
curl -X GET http://localhost:8000/health
```

### Step 2: Generate an article
```bash
curl -X POST http://localhost:8000/api/v1/articles/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Quantum computing breakthroughs in 2024"
  }'
```

### Step 3: View all articles
```bash
curl -X GET http://localhost:8000/api/v1/articles/list
```

### Step 4: Get statistics
```bash
curl -X GET http://localhost:8000/api/v1/stats
```

### Step 5: Download the article
```bash
curl -X GET http://localhost:8000/api/v1/articles/download-markdown \
  -o quantum_article.md && cat quantum_article.md
```

---

## 8. Error Handling Examples

### Invalid Topic (Too Short)
```bash
curl -X POST http://localhost:8000/api/v1/articles/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI"
  }'
```

**Expected Error Response:**
```json
{
  "detail": [
    {
      "loc": ["body", "topic"],
      "msg": "ensure this value has at least 3 characters",
      "type": "value_error.string.too_short"
    }
  ]
}
```

### Download with No Articles
```bash
curl -X GET http://localhost:8000/api/v1/articles/download-markdown
```

**Expected Response:**
```json
{
  "detail": "No completed article found for download."
}
```

---

## 9. Using Pretty JSON Output

### Make output readable with `jq`

```bash
# Install jq first (macOS):
brew install jq

# Pretty print response
curl -X GET http://localhost:8000/api/v1/stats | jq '.'

# Pretty print with indentation
curl -X POST http://localhost:8000/api/v1/articles/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "Machine Learning trends"}' | jq '.'

# Extract specific fields
curl -X GET http://localhost:8000/api/v1/stats | jq '.status_breakdown'
```

---

## 10. Save Responses to Files

### Save article to file
```bash
curl -X POST http://localhost:8000/api/v1/articles/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "Climate change solutions"}' \
  -o article_response.json

# View the file
cat article_response.json | jq '.'
```

### Save and extract article content
```bash
curl -X POST http://localhost:8000/api/v1/articles/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "Space exploration missions"}' | jq '.article' -r > article.txt
```

---

## 11. Monitoring API Performance

### Time the request
```bash
time curl -X POST http://localhost:8000/api/v1/articles/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "Renewable energy innovations"}'
```

### Check response headers
```bash
curl -X GET http://localhost:8000/api/v1/stats -v
```

### Watch API logs while making requests
```bash
# Terminal 1: Start the API with verbose logging
python3 main.py --mode api --host 0.0.0.0 --port 8000

# Terminal 2: Make requests while watching logs in Terminal 1
curl -X POST http://localhost:8000/api/v1/articles/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "Cryptocurrency market updates"}'
```

---

## 12. Batch Processing Multiple Topics

### Generate multiple articles in sequence

```bash
#!/bin/bash
topics=(
  "Artificial Intelligence innovations"
  "Blockchain technology applications"
  "Cybersecurity trends 2024"
  "Cloud computing evolution"
)

for topic in "${topics[@]}"; do
  echo "🔄 Generating article for: $topic"
  curl -X POST http://localhost:8000/api/v1/articles/generate \
    -H "Content-Type: application/json" \
    -d "{\"topic\": \"$topic\"}" \
    -o "article_${topic// /_}.json"
  echo "✅ Saved"
  sleep 2
done
```

Save as `batch_generate.sh` and run:
```bash
chmod +x batch_generate.sh
./batch_generate.sh
```

---

## Swagger Documentation

Once the API is running, access interactive documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

These provide a GUI to test all endpoints with real-time documentation.

---

## Troubleshooting

### Connection Refused
```bash
# Make sure the API is running
curl http://localhost:8000/health

# If it fails, restart the API
python3 main.py --mode api
```

### Timeout Error
- The article generation takes 2-3 minutes
- Use `curl --max-time 300` for longer timeouts:
```bash
curl --max-time 300 -X POST http://localhost:8000/api/v1/articles/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "Your topic"}'
```

### Missing Environment Variables
```bash
# Check if .env exists
cat .env

# Verify all keys are set
echo $GROQ_API_KEY
echo $TAVILY_API_KEY
```

---

## API Response Times

| Endpoint | Time |
|----------|------|
| `/health` | < 100ms |
| `/api/v1/articles/generate` | 2-3 minutes |
| `/api/v1/articles/list` | < 100ms |
| `/api/v1/stats` | < 100ms |
| `/api/v1/articles/download-markdown` | < 100ms |

---

**Happy testing! 🚀**
