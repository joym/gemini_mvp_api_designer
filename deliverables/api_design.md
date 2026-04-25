This API contract enables a FastAPI MVP for an intelligent learning assistant, focusing on observable adaptation.
## 1) Summary
*   **MVP Scope:** Focuses on a user's adaptive learning journey (explanations, quizzes, submit responses, and get the next step) through one concept at a time.
*   **Observable Adaptation:** API responses explicitly detail the learning state, adaptation decisions, and reasons for content changes.
*   **Core Loop:** Users start a session, receive a learning step, submit a response, and get the next adaptive step.
*   **Observability**: API responses explicitly include fields detailing the current learning state (difficulty, pace, progress) and the *reason* for content adaptation.
*   **Core Entities**: Concepts, Learning Sessions, Learning Steps, User Responses, and Adaptation Details.
*   **No Content Management:** Learning content (concepts, steps) is assumed to be pre-defined and managed externally.

### 2) Endpoints Table

| Method | Path | Learning Stage | Purpose | Key Inputs | Key Outputs | Idempotent | Notes |
|------|------|---------------|---------|------------|-------------|------------|-------|
| POST | /v1/sessions | Start Learning | Start a learning session for a user on a specific concept | user_id, concept_id | session_id, initial learning state | No | One active session per user–concept pair |
| GET | /v1/sessions/{session_id}/step | Deliver Content | Retrieve the current learning step based on session state | session_id | content, LearningSessionState, AdaptationDecision | Yes | Returns the same step until feedback is submitted |
| POST | /v1/sessions/{session_id}/response | Submit Feedback | Submit user response and self‑feedback for the current step | response, confidence, time_taken | updated state, adaptation decision | Yes (per step) | Primary adaptation trigger |
| GET | /v1/sessions/{session_id}/state | Inspect Progress | Retrieve the current learning state for observability or UI | session_id | LearningSessionState | Yes | Supports dashboards and client sync |
| POST | /v1/sessions/{session_id}/complete | Complete Learning | Mark the concept as completed for the user | session_id | final mastery state | No | Sets mastery_level to `mastered` |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ## Shared Models

### LearningSessionState

json
{
  "$id": "LearningSessionState",
  "type": "object",
  "properties": {
    "session_id": { "type": "string", "format": "uuid" },
    "concept_id": { "type": "string", "format": "uuid" },
    "current_step_id": { "type": "string", "format": "uuid" },

    "current_difficulty": {
      "type": "string",
      "enum": ["easy", "medium", "hard"]
    },
    "pace": {
      "type": "string",
      "enum": ["slow", "normal", "fast"]
    },
    "mastery_level": {
      "type": "string",
      "enum": ["learning", "practicing", "mastered"]
    },

    "accuracy_score": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Rolling accuracy score based on recent responses"
    },
    "attempt_count": {
      "type": "integer",
      "minimum": 0
    },
    "avg_response_time_sec": {
      "type": "number",
      "minimum": 0
    },
    "self_confidence": {
      "type": "integer",
      "minimum": 1,
      "maximum": 5
    }
  },
  "required": [
    "session_id",
    "concept_id",
    "current_step_id",
    "current_difficulty",
    "pace",
    "mastery_level",
    "accuracy_score",
    "attempt_count"
  ]
}


### AdaptationDecision
{
  "$id": "AdaptationDecision",
  "type": "object",
  "properties": {
    "next_step_type": {
      "type": "string",
      "enum": ["explanation", "example", "quiz", "review"]
    },
    "adjustment_reason": {
      "type": "string",
      "enum": [
        "low_accuracy",
        "high_accuracy",
        "low_confidence",
        "high_confidence",
        "slow_pace",
        "fast_pace"
      ]
    },
    "recommended_pace": {
      "type": "string",
      "enum": ["slow", "normal", "fast"]
    }
  },
  "required": ["next_step_type", "adjustment_reason"]
}

## LearningStepSuccessExample
{
  "session_state": {
    "session_id": "a3f1a7d2-4e0c-4f87-a93e-6b17c7af9c21",
    "concept_id": "b9e98e4d-12a4-4b41-9f0e-1c441dcbddfa",
    "current_step_id": "6f02db57-f7b2-4a4e-a4df-2f3f33b01c10",
    "current_difficulty": "easy",
    "pace": "slow",
    "mastery_level": "learning",
    "accuracy_score": 0.45,
    "attempt_count": 3,
    "avg_response_time_sec": 42,
    "self_confidence": 2
  },
  "adaptation": {
    "next_step_type": "explanation",
    "adjustment_reason": "low_accuracy",
    "recommended_pace": "slow"
  },
  "content": {
    "title": "Concept Explanation",
    "body": "Let’s revisit the core idea with a simpler explanation and an additional example."
  }
}

## ErrorResponse
{
  "$id": "ErrorResponse",
  "type": "object",
  "properties": {
    "error_code": { "type": "string" },
    "message": { "type": "string" }
  },
  "required": ["error_code", "message"]
}

## ErrorExample_BadRequest
{
  "error_code": "INVALID_INPUT",
  "message": "The submitted response is missing required fields or contains invalid values."
}

**Response Codes:**
- 200 OK – Successful retrieval or update
- 400 Bad Request – Invalid input payload
- 404 Not Found – Session or resource not found


## Implementation Notes

### Efficiency
- List-style endpoints may support cursor-based pagination in future iterations.
- Learning step submission is idempotent per step identifier.
- Responses are intentionally lightweight to minimize payload size and latency.
- Idempotent endpoints may accept an `Idempotency-Key` header to safely retry requests.

### Security
- Authentication and authorization are assumed to be handled by an upstream gateway (e.g., OAuth2 / JWT).
- The API focuses on learning logic and trusts the `user_id` from the authenticated context.
- Rate limiting and request validation are expected to be enforced at the gateway layer.

### Accessibility & Compatibility
- All endpoints are versioned under `/v1` to support backward compatibility.
- Learning content is language-agnostic and can support localization in future iterations.
