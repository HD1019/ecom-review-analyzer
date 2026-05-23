# E-commerce Review Analyzer

AI-powered e-commerce review analysis API. Extract structured insights from customer feedback — strengths, weaknesses, buyer personas, and sentiment distribution — all in a single API call.

[![RapidAPI](https://img.shields.io/badge/RapidAPI-Get%20API-blue)](https://rapidapi.com/hd1019/api/e-commerce-review-analyzer)
[![Railway](https://img.shields.io/badge/Railway-Deploy-green)](https://ecom-review-analyzer-production.up.railway.app)

## Overview

Harness large language models to automatically analyze batches of customer reviews. Instead of manually reading through hundreds of reviews, get a consolidated, actionable report in seconds.

### Returns

- **Strengths & Weaknesses** — Each finding includes a verbatim customer quote
- **Severity Ratings** — Weaknesses tagged High / Medium / Low
- **Buyer Persona** — Under 50 words, synthesized from review patterns
- **Sentiment Distribution** — Positive / Negative / Neutral ratios
- **Improvement Suggestion** — The single most impactful recommendation

## Quick Start

```bash
curl -X POST https://ecommerce-review-analyzer.p.rapidapi.com/api/v1/analyze-reviews \
  -H "X-RapidAPI-Key: YOUR_API_KEY" \
  -H "X-RapidAPI-Host: ecommerce-review-analyzer.p.rapidapi.com" \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Wireless Earbuds Pro",
    "reviews": [
      "Amazing noise cancellation, the world just goes silent",
      "Battery lasts forever, perfect for business trips",
      "Connection drops 3-5 times on the subway, really frustrating",
      "Ear tips are too stiff, hurts after 2 hours"
    ],
    "max_reviews": 10
  }'
```

### Response

```json
{
  "product_name": "Wireless Earbuds Pro",
  "analyzed_count": 4,
  "total_count": 4,
  "analysis": {
    "strengths": [
      "Noise cancellation is top-tier: 'Amazing noise cancellation, the world just goes silent'",
      "Excellent battery life: 'Battery lasts forever, perfect for business trips'"
    ],
    "weaknesses": [
      "Connection instability (High): 'Connection drops 3-5 times on the subway'",
      "Poor long-term comfort (Medium): 'Ear tips are too stiff, hurts after 2 hours'"
    ],
    "improvement_suggestions": "Prioritize Bluetooth stability improvements in high-interference environments and switch to softer ear tip materials.",
    "user_profile": "Value-conscious commuters and travelers who prioritize ANC and battery endurance over comfort.",
    "sentiment_distribution": {
      "positive": 0.5,
      "negative": 0.5,
      "neutral": 0.0
    }
  }
}
```

## Python Example

```python
import requests

url = "https://ecommerce-review-analyzer.p.rapidapi.com/api/v1/analyze-reviews"

payload = {
    "product_name": "Wireless Earbuds Pro",
    "reviews": [
        "Amazing noise cancellation!",
        "Connection drops on subway",
        "Battery lasts forever"
    ],
    "max_reviews": 10
}

headers = {
    "X-RapidAPI-Key": "YOUR_API_KEY",
    "X-RapidAPI-Host": "ecommerce-review-analyzer.p.rapidapi.com",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

## Node.js Example

```javascript
const axios = require('axios');

const options = {
  method: 'POST',
  url: 'https://ecommerce-review-analyzer.p.rapidapi.com/api/v1/analyze-reviews',
  headers: {
    'X-RapidAPI-Key': 'YOUR_API_KEY',
    'X-RapidAPI-Host': 'ecommerce-review-analyzer.p.rapidapi.com',
    'Content-Type': 'application/json'
  },
  data: {
    product_name: 'Wireless Earbuds Pro',
    reviews: [
      'Amazing noise cancellation!',
      'Connection drops on subway',
      'Battery lasts forever'
    ],
    max_reviews: 10
  }
};

axios.request(options).then(res => console.log(res.data));
```

## API Reference

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `product_name` | string | No | — | Product name for context in the analysis prompt |
| `reviews` | string[] | **Yes** | — | List of customer review texts (min 1 item) |
| `max_reviews` | integer | No | 100 | Max reviews to analyze (1–300) |

### Error Codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 400 | Invalid request body |
| 401 | Missing or invalid auth token |
| 429 | Monthly quota exceeded |
| 502 | LLM provider unreachable |

## Pricing

Available on RapidAPI Hub:

| Plan | Price | Requests/Month |
|---|---|---|
| Free | $0 | 20 |
| Basic | $9.99 | 500 |
| Pro | $29.99 | 2,000 |
| Enterprise | $99.99 | 10,000 |

## Self-Hosting

```bash
# Clone
git clone https://github.com/HD1019/ecom-review-analyzer.git
cd ecom-review-analyzer

# Install
pip install -r requirements.txt

# Set env vars
export LLM_API_KEY=sk-your-key
export LLM_MODEL=deepseek-chat
export ADMIN_API_KEY=admin-key-123

# Run
uvicorn app:app --host 0.0.0.0 --port 8000
```

Supports any OpenAI-compatible LLM (DeepSeek, OpenAI, Ollama, vLLM). Configure via `LLM_BASE_URL`.

## Tech Stack

- FastAPI + Pydantic
- SQLite (multi-key management)
- Docker + Railway (deployment)
- OpenAI-compatible LLM backend

## License

MIT
