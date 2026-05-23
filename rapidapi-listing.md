# E-commerce Review Analyzer

Transform raw customer reviews into actionable business insights with AI-powered analysis. Get structured sentiment breakdowns, strength/weakness extraction, and data-driven improvement recommendations in a single API call.

---

## Short Description

Harness AI to automatically analyze e-commerce product reviews. Extract key strengths and weaknesses with severity ratings, generate buyer personas, measure sentiment distribution, and receive a prioritized improvement suggestion — all from one endpoint. Perfect for product managers, e-commerce operators, and brand strategists.

---

## Detailed Description

### What It Does

E-commerce Review Analyzer uses state-of-the-art large language models to process batches of customer reviews and return a structured, actionable analysis. Instead of manually reading through hundreds of reviews, you get a consolidated report in seconds.

### Key Features

- **Strength & Weakness Extraction** — Each finding includes a representative verbatim quote from actual reviews, so you know exactly what customers said.
- **Severity Ratings** — Every weakness is tagged with High / Medium / Low severity, helping you prioritize fixes.
- **Buyer Persona Generation** — The model synthesizes a concise user profile describing who your typical customer is (under 50 words).
- **Sentiment Distribution** — Get a quantitative breakdown of positive, negative, and neutral sentiment across all analyzed reviews.
- **Prioritized Improvement Suggestion** — Receive a single, most-impactful recommendation distilled from all feedback.

### Use Cases

| Scenario | How It Helps |
|---|---|
| **Product launch post-mortem** | Analyze early reviews to decide what to fix in the next batch. |
| **Competitor intelligence** | Scrape competitor reviews and understand their product's weak spots. |
| **Customer support triage** | Identify recurring pain points before they escalate into refunds. |
| **Marketing copy optimization** | Use extracted strengths and user profiles to sharpen product messaging. |
| **Supply chain decisions** | Spot hardware/quality issues early from negative sentiment patterns. |

### Why This API?

Most review analysis tools only return raw sentiment scores. Our API goes deeper — it produces an **operations-ready report** that connects each finding to real customer language, assigns severity, and tells you *what to do next*. Built on the same models powering modern AI assistants, the analysis is nuanced, context-aware, and production-hardened with automatic JSON parsing and retry logic.

---

## API Endpoint

| Method | Path |
|---|---|
| `POST` | `/api/v1/analyze-reviews` |

**Base URL:** `https://ecom-review-analyzer.up.railway.app` (self-hosted) or your RapidAPI-provisioned endpoint.

---

## Authentication

All requests require a Bearer token in the `Authorization` header.

```
Authorization: Bearer <YOUR_API_KEY>
```

Your API key is provisioned when you subscribe to a plan. Keep it secure — do not expose it in client-side code.

---

## Request Body

Content-Type: `application/json`

| Field | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `product_name` | `string` | No | `null` | — | Name of the product being analyzed. Included in the prompt for context. |
| `reviews` | `string[]` | **Yes** | — | Min 1 item, non-empty strings | List of user reviews. Empty or whitespace-only strings are filtered out. |
| `max_reviews` | `integer` | No | `100` | 1–300 | Maximum number of reviews to process. The first N reviews are analyzed; extras are ignored. |

### Example Request Body

```json
{
  "product_name": "SoundCore Pro Wireless Earbuds",
  "reviews": [
    "Amazing noise cancellation, the world just goes silent. Low-frequency filtering is incredible.",
    "Sound quality is decent but connection drops 3-5 times on the subway — really frustrating.",
    "Battery lasts a full week with heavy use. Perfect for business trips.",
    "Ear tips are too stiff, starts hurting after 2 hours. Please improve the material.",
    "Unbeatable value at this price point. Already recommended to my whole team.",
    "Sleek matte case feels premium. Gave it to my girlfriend and she loved it.",
    "Call quality is mediocre, the other side hears echo. Not great for work calls.",
    "Touch controls are responsive but prone to accidental triggers. Needs a lock mode.",
    "Unboxing experience was premium — included a travel pouch and multiple tip sizes.",
    "Bluetooth 5.3 pairing is instant, latency is negligible even for gaming."
  ],
  "max_reviews": 10
}
```

---

## Response

### Success Response — `200 OK`

```json
{
  "product_name": "SoundCore Pro Wireless Earbuds",
  "analyzed_count": 10,
  "total_count": 10,
  "analysis": {
    "strengths": [
      "Noise cancellation is top-tier: 'Amazing noise cancellation, the world just goes silent'",
      "Excellent battery life: 'Battery lasts a full week with heavy use'",
      "Great value for money: 'Unbeatable value at this price point'",
      "Premium design and unboxing: 'Sleek matte case feels premium'",
      "Fast Bluetooth pairing: 'Bluetooth 5.3 pairing is instant, latency is negligible'"
    ],
    "weaknesses": [
      "Connection stability issues (High): 'connection drops 3-5 times on the subway'",
      "Poor long-term comfort (Medium): 'starts hurting after 2 hours'",
      "Subpar call quality (Medium): 'the other side hears echo'",
      "Accidental touch triggers (Low): 'prone to accidental triggers'"
    ],
    "improvement_suggestions": "Prioritize Bluetooth connection stability improvements, especially in high-interference environments like public transit, and consider softer ear tip materials to improve long-wear comfort.",
    "user_profile": "Value-conscious power users who prioritize ANC and battery life for daily commuting and travel. They care about build quality, comfort, and expect reliable connectivity.",
    "sentiment_distribution": {
      "positive": 0.5,
      "negative": 0.3,
      "neutral": 0.2
    }
  }
}
```

### Response Fields

| Field | Type | Description |
|---|---|---|
| `product_name` | `string \| null` | Echoes the product name from the request. |
| `analyzed_count` | `integer` | Number of reviews actually processed (after applying `max_reviews`). |
| `total_count` | `integer` | Total number of reviews submitted in the request. |
| `analysis.strengths` | `string[]` | Extracted strengths, each with a verbatim customer quote. |
| `analysis.weaknesses` | `string[]` | Extracted weaknesses, each tagged with severity (High/Medium/Low) and a verbatim quote. |
| `analysis.improvement_suggestions` | `string` | The single most impactful recommendation for the product team. |
| `analysis.user_profile` | `string` | Concise buyer persona (≤50 Chinese characters or equivalent). |
| `analysis.sentiment_distribution` | `object` | Sentiment ratios: `positive`, `negative`, `neutral` (sum ≈ 1.0). |

### Error Responses

| Status Code | Meaning | Example Body |
|---|---|---|
| `400 Bad Request` | Invalid request body (missing required fields, empty reviews, `max_reviews` out of range). | `{"detail": "评论列表不能全为空"}` |
| `401 Unauthorized` | Missing or invalid Bearer token. | `{"detail": "缺少有效的认证令牌"}` |
| `500 Internal Server Error` | LLM returned unparseable JSON (rare, automatically retried). | `{"detail": "大模型返回结果解析失败"}` |
| `502 Bad Gateway` | Upstream LLM provider is unreachable or returned an error. | `{"detail": "无法连接到大模型服务"}` |

---

## Usage Example (curl)

```bash
curl -X POST https://ecom-review-analyzer.up.railway.app/api/v1/analyze-reviews \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Wireless Mouse X1",
    "reviews": [
      "Super comfortable for all-day use, no wrist strain at all",
      "Scroll wheel started squeaking after a month, pretty annoying",
      "Battery lasts forever, forgot when I last changed it",
      "Great value, feels more expensive than it is"
    ],
    "max_reviews": 50
  }'
```

### Python Example

```python
import requests

API_KEY = "your-api-key-here"
URL = "https://ecom-review-analyzer.up.railway.app/api/v1/analyze-reviews"

payload = {
    "product_name": "Wireless Mouse X1",
    "reviews": [
        "Super comfortable for all-day use",
        "Scroll wheel started squeaking after a month",
        "Battery lasts forever",
        "Great value, feels premium"
    ],
    "max_reviews": 50
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

response = requests.post(URL, json=payload, headers=headers, timeout=120)
print(response.json())
```

---

## Pricing Plans

| Plan | Price | Requests / Month | Rate Limit | Best For |
|---|---|---|---|---|
| **Free** | $0 | 20 | 1 req / min | Testing and evaluation |
| **Basic** | $9.99 | 500 | 10 req / min | Solo developers, small shops |
| **Pro** | $29.99 | 2,000 | 30 req / min | Growing e-commerce brands |
| **Enterprise** | $99.99 | 10,000 | 100 req / min | Agencies, multi-brand operators |

All plans include:
- Up to **300 reviews per request** (configured via `max_reviews`)
- Full analysis output (strengths, weaknesses, suggestions, persona, sentiment)
- 120-second request timeout per call
- Email support (Enterprise: priority Slack channel)

Overage: $0.05 per additional request on Basic/Pro plans. Enterprise overages billed at custom rate.

---

## FAQ

### How long does a typical request take?

Most requests complete in 5–15 seconds. Processing time scales with the number of reviews; analyzing 300 reviews typically takes 20–40 seconds. The API timeout is 120 seconds.

### What languages are supported for reviews?

The underlying LLM handles **all major languages** including English, Chinese, Spanish, French, German, Japanese, and Korean. The analysis output language will match the predominant language of the reviews.

### Can I analyze reviews from any e-commerce platform?

Yes. The API is platform-agnostic. Whether your reviews come from Amazon, Shopify, AliExpress, or your own store, just pass them as a string array.

### How is "severity" determined?

The LLM assigns severity based on: (1) frequency of the complaint across reviews, (2) impact on purchase decisions, and (3) whether the issue affects core functionality. **High** = deal-breaker, **Medium** = noticeable friction, **Low** = minor annoyance.

### What happens if the LLM returns malformed JSON?

The service includes a two-stage parsing pipeline: direct JSON parse first, then Markdown code block extraction as fallback. If both fail, a `500` error is returned. This happens in <0.1% of requests.

### Is my data used to train the model?

No. We route requests through provider APIs (DeepSeek by default) with training opt-out. Review data is processed in-memory and never persisted or logged beyond the request lifecycle.

### Can I use my own LLM provider?

Yes. The `LLM_BASE_URL` and `LLM_MODEL` environment variables let you point to any OpenAI-compatible endpoint (OpenAI, DeepSeek, Ollama, vLLM, etc.). Self-hosted deployments have full control.

### How do I upgrade or cancel my plan?

Manage your subscription directly on your [RapidAPI Dashboard](https://rapidapi.com/developer/dashboard). Upgrades take effect immediately; downgrades apply at the end of the current billing cycle.
