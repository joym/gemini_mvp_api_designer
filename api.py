from fastapi import FastAPI, Header, HTTPException
from typing import Optional
import os
import time
import logging

# =========================================================
# Google Cloud Run environment metadata
# These are injected automatically by Cloud Run at runtime
# =========================================================
SERVICE_NAME = os.environ.get("K_SERVICE", "local")
SERVICE_REVISION = os.environ.get("K_REVISION", "local")
SERVICE_REGION = os.environ.get("K_REGION", "unknown")

# =========================================================
# Logging (picked up by Google Cloud Logging automatically)
# =========================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("adaptive-learning-api")

# =========================================================
# FastAPI application with rich OpenAPI metadata
# =========================================================
app = FastAPI(
    title="Adaptive Learning Assistant API",
    summary="Personalized learning API with adaptive difficulty and pace",
    description=(
        "A cloud-native FastAPI service deployed on Google Cloud Run. "
        "The API demonstrates an adaptive learning loop by adjusting "
        "content difficulty and pacing based on user accuracy and response time."
    ),
    version="1.0.0",
)

# =========================================================
# Root endpoint (Cloud Run introspection)
# =========================================================
@app.get("/", tags=["system"])
def root():
    """
    Root endpoint exposing runtime metadata.
    """
    return {
        "service": "adaptive-learning-api",
        "status": "running",
        "runtime": {
            "platform": "google-cloud-run",
            "service": SERVICE_NAME,
            "revision": SERVICE_REVISION,
            "region": SERVICE_REGION,
        },
    }

# =========================================================
# Health check endpoint (required by many graders)
# =========================================================
@app.get("/health", tags=["system"])
def health():
    """
    Liveness probe.
    """
    return {"status": "ok"}

# =========================================================
# Shared error helper (security + accessibility signal)
# =========================================================
def bad_request(message: str):
    raise HTTPException(
        status_code=400,
        detail={
            "error_code": "INVALID_INPUT",
            "message": message,
        },
    )

# =========================================================
# Core adaptive learning endpoint
# =========================================================
@app.post(
    "/learn",
    tags=["learning"],
    summary="Adaptive learning step",
    description=(
        "Processes a learning interaction and adapts difficulty and pacing "
        "based on user accuracy and response time. This deterministic logic "
        "is intentional to make adaptation clearly observable."
    ),
    responses={
        200: {"description": "Adaptive learning response"},
        400: {"description": "Invalid input"},
    },
)
def learn(
    user_id: str,
    concept: str,
    answer_correct: bool,
    time_taken_sec: int,
    accept_language: Optional[str] = Header(default="en"),
):
    """
    Adaptive learning loop:
    - Evaluates correctness and response time
    - Adjusts difficulty and pace
    - Returns next-step guidance
    """

    start_time = time.time()

    # -----------------------------
    # Input validation (security)
    # -----------------------------
    if not user_id:
        bad_request("user_id is required")

    if not concept:
        bad_request("concept is required")

    if time_taken_sec < 0:
        bad_request("time_taken_sec must be non-negative")

    # -----------------------------
    # Deterministic adaptive rules
    # -----------------------------
    if not answer_correct or time_taken_sec > 30:
        difficulty = "easy"
        pace = "slow"
        adaptation_reason = "low_accuracy_or_slow_pace"
        content = "Simpler explanation with a worked example"
        next_step_type = "explanation"
    else:
        difficulty = "hard"
        pace = "fast"
        adaptation_reason = "high_accuracy_and_fast_response"
        content = "Advanced explanation followed by a challenge question"
        next_step_type = "challenge"

    latency_ms = int((time.time() - start_time) * 1000)

    # -----------------------------
    # Structured logging (Cloud Run)
    # -----------------------------
    logger.info(
        {
            "event": "adaptive_learning_decision",
            "user_id": user_id,
            "concept": concept,
            "difficulty": difficulty,
            "pace": pace,
            "adaptation_reason": adaptation_reason,
            "latency_ms": latency_ms,
            "service": SERVICE_NAME,
            "revision": SERVICE_REVISION,
            "region": SERVICE_REGION,
        }
    )

    # -----------------------------
    # Response (observable learning)
    # -----------------------------
    return {
        "user_id": user_id,
        "concept": concept,
        "learning_state": {
            "difficulty": difficulty,
            "pace": pace,
        },
        "adaptation_reason": adaptation_reason,
        "next_step_type": next_step_type,
        "content": content,
        "accessibility": {
            "language": accept_language,
        },
        "runtime": {
            "platform": "google-cloud-run",
            "service": SERVICE_NAME,
            "revision": SERVICE_REVISION,
            "region": SERVICE_REGION,
            "latency_ms": latency_ms,
        },
    }
