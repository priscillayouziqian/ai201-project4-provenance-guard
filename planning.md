# Provenance Guard — Planning

## Architecture Narrative

A submitted piece of text travels through the following components:

1. **Validation** — Check that the content is not empty and meets minimum length requirements.
2. **Detection Pipeline** — Two signals run in parallel:
   - Signal 1 (Groq LLM): Evaluates semantic style and coherence; returns a score from 0–1.
   - Signal 2 (Stylometric Heuristics): Computes statistical features (sentence length variance, type-token ratio); returns a score from 0–1.
3. **Confidence Scoring** — Weighted average: Groq × 0.6 + Stylometric × 0.4 = final score.
4. **Transparency Label** — Final score maps to one of three plain-language labels shown to the user.
5. **Audit Log** — Every decision is recorded with content ID, timestamp, signal scores, final score, and label.

## Detection Signals

### Signal 1: Stylometric Heuristics
- **What**: Measures sentence length variance and type-token ratio (vocabulary diversity).
- **Why**: AI writing tends to be structurally uniform; human writing varies naturally in rhythm and length.
- **Blind spot**: Professional writers who deliberately write with consistent structure may be misclassified as AI.
- **Output format**: float between 0.0 and 1.0
- **Weight**: 0.4

### Signal 2: Groq LLM Classification
- **What**: Asks a large language model to assess whether the text reads as human or AI-generated, based on semantic style and coherence.
- **Why**: AI writing has recognizable patterns — overly smooth transitions, complete structure, "safe" word choices.
- **Blind spot**: Content from different AI models may evade detection; AI content heavily edited by humans may also be misclassified.
- **Output format**: float between 0.0 and 1.0
- **Weight**: 0.6

### Why These Two Together
The two signals have different blind spots and measure independent properties
(structural vs. semantic), making their combination more reliable than either alone.

### Confidence Scoring
Final score = (Groq score × 0.6) + (Stylometric score × 0.4)

### Thresholds
| Score Range | Interpretation |
|---|---|
| > 0.70 | High confidence: AI-generated |
| 0.40 – 0.70 | Uncertain |
| < 0.40 | High confidence: Human-written |

Thresholds are intentionally asymmetric. The uncertain band is wide to reduce
false positives — mislabeling a human creator's work as AI is worse than
missing an AI-generated piece.

## API Endpoints

### POST /submit
- **Accepts**: `{ "content": "text body" }`
- **Returns**: `{ "content_id", "result", "confidence_score", "label" }`

### POST /appeal
- **Accepts**: `{ "content_id": "xxx", "reason": "appeal explanation" }`
- **Returns**: `{ "content_id", "status": "under review", "message": "Appeal received" }`

### GET /log
- **Accepts**: optional query parameter `?content_id=xxx`
- **Returns**: `{ "logs": [ { "content_id", "timestamp", "groq_score",
  "stylometric_score", "final_score", "label", "appeal_status" } ] }`
  
## Architecture
### Submission Flow

```
User
  |
  | (raw text)
  v
POST /submit
  |
  | (validated text)
  v
[Validation]
  |
  | (clean text)
  v
[Detection Pipeline]
  |              |
  | (text)       | (text)
  v              v
[Groq LLM]   [Stylometric]
  |              |
  | (0-1 score)  | (0-1 score)
  └──────┬───────┘
         | (two scores)
         v
  [Confidence Scoring]
  (Groq×0.6 + Stylo×0.4)
         |
         | (final score 0-1)
         v
  [Transparency Label]
  (>0.70 / 0.4-0.70 / <0.4)
         |
         | (label text)
         v
    [Audit Log]
         |
         | (full result)
         v
     Response to User
```

### Appeal Flow

```
User
  |
  | (content_id + reason)
  v
POST /appeal
  |
  | (find original record)
  v
[Status Update]
(status → "under review")
  |
  | (updated record)
  v
[Audit Log]
(log appeal reason + new status)
  |
  | (confirmation)
  v
Response to User
```


## Transparency Labels

### High-confidence AI (score > 0.75)
"Our system believes this content was created by AI. Confidence: High.
If you are the creator and believe this is incorrect, you may submit an appeal."

### Uncertain (score 0.40 – 0.75)
"Our system was unable to confidently determine whether this content was
written by a human or AI. If you are the creator, you may submit an appeal
to provide more context."

### High-confidence Human (score < 0.40)
"Our system believes this content was created by a human. Confidence: High.
If you believe this assessment is incorrect, you may submit an appeal."

---

## Appeals Workflow

- **Who can appeal**: Any creator who submitted content and disagrees with
  the classification result.
- **What they provide**: `content_id` + `reason` (written explanation)
- **What the system does**:
  1. Updates content status to `under review`
  2. Logs the appeal reason, timestamp, and original decision to the audit log
- **What a human reviewer sees**: content_id, original label, confidence score,
  both signal scores, appeal reason, and timestamp

---

## Edge Cases

1. **Simple or repetitive poetry**: A human-written poem using plain vocabulary
   and repetition may be flagged as AI by stylometric heuristics due to low
   type-token ratio and uniform sentence length.

2. **Humanized AI content**: AI-generated text passed through humanization tools
   (e.g. Quillbot, Undetectable.ai) may exhibit higher sentence variance and
   vocabulary diversity, causing both signals to underestimate AI likelihood.

---

## AI Tool Plan

### M3 — Submission Endpoint + Signal 1 (Groq)
- **Spec sections to provide**: Detection Signals + Architecture diagram
- **What to ask for**: Flask app skeleton + `/submit` endpoint +
  Groq signal function
- **How to verify**: Test with 3 inputs (clear AI text, clear human text,
  ambiguous text) and check that Groq returns a float between 0.0 and 1.0

### M4 — Signal 2 + Confidence Scoring
- **Spec sections to provide**: Detection Signals + Uncertainty Representation
  + Architecture diagram
- **What to ask for**: Stylometric heuristics function + weighted
  confidence scoring logic
- **How to verify**: Check that scores vary meaningfully between clearly AI
  and clearly human text; confirm final score uses correct weights

### M5 — Production Layer
- **Spec sections to provide**: Transparency Labels + Appeals Workflow
  + Architecture diagram
- **What to ask for**: Label generation logic + `/appeal` endpoint +
  `/log` endpoint + rate limiting + audit log
- **How to verify**: Confirm all three label variants are reachable;
  test that appeal submission updates status to "under review";
  check audit log captures all required fields