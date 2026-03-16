# QA Test Generator — Tool Architecture

## Overview

This document describes the high-level architecture, main components, data flows, and extension points for the QA Test Generator project (the Streamlit UI + backend services that extract Figma data, parse PRDs, and generate AI-powered test cases).

## Components

- **Streamlit UI (`demo_ui.py`)**: user-facing interface for entering Figma file URL, tokens, loading caches, uploading PRDs, triggering analysis and test generation, and exporting results.
- **Configuration (`app/config.py`)**: centralizes environment-driven settings such as API keys, cache locations, and feature toggles.
- **Figma Client (`app/services/figma_client.py`)**: fetches design JSON from Figma API and normalizes the payload for downstream processing. Handles pagination and rate-limit backoff.
- **Cache Manager (`app/services/cache_manager.py`)**: reads/writes cached Figma payloads and intermediate results to disk to avoid repeated API calls; exposes load/save/evict operations.
- **Document Parser (`app/services/document_parser.py`)**: extracts textual requirements and structured data from uploaded PRDs (PDF, DOCX, TXT) and returns cleaned context for the generator.
- **PRD Analyzer (`app/services/prd_analyzer.py`)**: augments and maps parsed PRD sections to UI screens/components to create traceability metadata.
- **Test Generator (`app/services/test_generator.py`)**: composes prompts, baseline scenarios, and context to call the AI model (Gemini/Claude) and converts responses into structured test case objects.
- **Evaluator (`app/services/evaluator.py`)**: optional post-processing pass that scores or filters generated tests for relevancy, duplicates, and coverage against baseline scenarios.
- **JSON Loader / Helpers (`app/services/json_loader.py`)**: utilities for reading/writing JSON artifacts (exported test sets, caches, baselines).
- **Baseline Data (`app/data/test_baseline.json`)**: curated list of domain test scenarios used to enrich AI outputs and ensure industry-standard coverage.

## Data Flow / Process

1. User enters a Figma file URL and token in the Streamlit UI and clicks 'Fetch & Cache'.
2. `figma_client` requests design JSON from Figma; `cache_manager` stores the raw payload.
3. User optionally uploads a PRD file. `document_parser` extracts and cleans text; `prd_analyzer` maps requirements to UI screens.
4. UI presents screens/components. User selects a screen and clicks 'Generate Test Cases'.
5. `test_generator` assembles context:
   - selected screen JSON (components metadata)
   - PRD-derived context and traceability hints
   - baseline scenarios from `test_baseline.json`
   - generation parameters (temperature, max tokens)
6. AI model is called with the assembled prompt; the raw response is parsed into structured test objects.
7. `evaluator` optionally scores and filters tests (duplicates, low-relevance), enriching each test with metadata (priority, tags, trace links).
8. Results shown in UI; user can review and click 'Export as JSON' which triggers `json_loader` to save the exported artifact.

## Error Handling & Resilience

- **Network / API Errors**: `figma_client` retries with exponential backoff; failures are surfaced to the UI with actionable messages.
- **Rate Limits**: `cache_manager` encourages cached workflow; `figma_client` respects Retry-After headers and backs off.
- **Parsing Failures**: `document_parser` returns best-effort text with warnings; UI shows upload parsing logs.
- **AI Failures**: `test_generator` has retry logic and validation; invalid AI output triggers a secondary prompt to reformat.

## Security & Configuration

- Secrets are loaded from environment variables (`.env`) via `app/config.py` (e.g., `FIGMA_ACCESS_TOKEN`, `GEMINI_API_KEY`). Do not commit `.env`.
- Limit token exposure in logs; redact API keys when logging.

## Scaling & Deployment

- For heavier use, split the architecture into services: UI (Streamlit) as a front-end, backend workers (Figma fetcher, generator) behind a queue (Redis/RabbitMQ). Store caches in durable storage (S3) and metadata in a lightweight DB (SQLite/Postgres).
- Use rate-limiters and concurrency controls for API calls to external LLMs and Figma.

## Extensibility Points

- Swap LLM provider: implement a provider abstraction in `test_generator` to support multiple model APIs.
- Add new parsers: `document_parser` is pluggable to add extra file formats (HTML, Markdown).
- Enhance evaluator rules: add custom business-rules for test prioritization and coverage metrics.

## Observability

- Add structured logging around key operations (fetch, parse, generate, export).
- Emit events for metrics (cache hit/miss, generation latency, error rates) to support monitoring.

## Quick Onboarding Checklist

- copy `.env.example` → `.env` and populate API keys
- `pip install -r requirements.txt`
- run UI: `streamlit run demo_ui.py`

## Summary

This architecture favors a modular, cache-first approach: fetch once, analyze locally, and synthesize tests by combining baseline knowledge with AI-driven generation. The structure in `app/services` isolates concerns, making the tool easy to extend and scale.
