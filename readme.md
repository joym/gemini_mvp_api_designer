# Intelligent Learning Assistant API

This repository contains a demo-ready FastAPI MVP for an intelligent learning assistant that adapts content based on user pace and understanding.

## Overview
The system demonstrates an adaptive learning loop:
1. A user starts learning a concept
2. The system delivers learning steps (explanations, quizzes)
3. The user submits responses and feedback
4. The system adapts the next step accordingly

## Deployment
- Designed as a stateless FastAPI application
- Deployed on Google Cloud Run for managed scalability and availability
- No local state is required; each request is handled independently

## Repository Structure
- `api.py` – FastAPI application entry point
- `deliverables/api_design.md` – Final API contract submission
- `tests/` – Minimal test suite for validation
- `Dockerfile` – Container definition for Cloud Run
