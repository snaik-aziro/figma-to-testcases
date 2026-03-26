# QA Test Generator - Angular UI

Enterprise Angular 17+ frontend scaffold for the internal "QA Test Generator" tool.

## High-level ASCII Architecture

Browser (Angular App) -> REST API Backend

App Shell:
- `AppComponent` (TopBar + Sidebar + Content)
- Pages: `Dashboard`, `GenerateTest`, `TestList`, `Settings`

## UI-to-API Mapping

| UI Component | User Action | API Endpoint | Method | Request Body | Response |
|--------------|-------------|--------------|--------|--------------|----------|
| GenerateTestComponent | Submit request to create tests | `/api/tests/generate` | POST | `{ screenId, options }` | `{ testId, status, tests: [...] }` |
| TestListComponent | Fetch generated tests | `/api/tests` | GET | — | `[{ testId, name, status }]` |
| DashboardComponent | Fetch summary metrics | `/api/dashboard/summary` | GET | — | `{ activeJobs, lastRun, failures }` |
| Sidebar | Fetch screens list | `/api/screens` | GET | — | `[{ screenId, name }]` |

## Example API request/response

POST `/api/tests/generate` request:

```json
{
  "screenId": "screen_123",
  "options": { "depth": "medium", "includeEdgeCases": true }
}
```

Response:

```json
{
  "testId": "tst_789",
  "status": "queued",
  "tests": []
}
```

## Supported Backend Endpoints (current server)

The UI should call the backend endpoints below — these are the endpoints currently implemented in `server.py`.

- POST `/api/figma/fetch-cache` — Fetch a Figma file and cache the extracted screens
  - Request body: `{ "fileUrlOrId": "<file_url_or_id>", "token": "<optional_figma_token>" }`
  - Response: `{ "cacheId": "<file_id>", "fileId": "<file_id>", "screensCount": 12 }`

- GET `/api/figma/cache` — List cached files (metadata)
  - Response: `[{ "file_id": "<file_id>", "file_name": "...", "cached_at": "..." }, ...]`

- GET `/api/figma/cache/{cacheId}` — Retrieve cached JSON for a file
  - Response: `{ "cacheId": "<file_id>", "data": { "screens": [ ... ] } }`

- DELETE `/api/figma/cache/{cacheId}` — Delete a cached file
  - Response: `{ "cacheId": "<file_id>", "status": "deleted" }`

- POST `/api/tests/generate` — Generate tests from a cached screen
  - Request body: `{ "cacheId": "<file_id>", "screenId": "<figma_node_id>", "testType": "functional", "testCount": 5 }`
  - Response: `{ "runId": "run_...", "testCount": 5, "tests": [ ... ] }`

- GET `/api/tests/runs` — List generated test run IDs
  - Response: `{ "runs": ["run_20260317T...", ...] }`

- GET `/api/tests/runs/{runId}` — Retrieve a saved run snapshot (generated tests)
  - Response: `{ "run_id": "...", "cache_id": "...", "screen_id": "...", "tests": [ ... ] }`

- GET `/api/tests/runs/{runId}/download` — Download run JSON
  - Response: JSON content (application/json)

- POST `/api/tests/evaluate` — Evaluate tests using the Evaluator (existing endpoint)
  - Request body: `{ "prd": {...}, "tests": {...}, "screen": {...}, "prefer_premium": false }`
  - Response: evaluator result object

Notes:
- These endpoints currently run synchronously: `/api/figma/fetch-cache` returns the cacheId after fetching; there is no background job/status endpoint implemented. If you need polling/progress, we can add a job/status flow.
- For security, prefer server-side `FIGMA_ACCESS_TOKEN` usage; the endpoint accepts an optional token but sending tokens from the client is not recommended.

## How to run locally

1. Install Node 20+ and npm/yarn
2. `cd qa-angular-ui`
3. `npm install`
4. `npm run start` — serves on `http://localhost:4200`

The frontend expects the backend root to be set in `src/environments/environment.ts`.

## Environment configuration

- `src/environments/environment.ts` — development `apiBaseUrl`.
- `src/environments/environment.prod.ts` — production `apiBaseUrl`.

## How backend team should align

- Provide REST endpoints under `apiBaseUrl` and follow request/response formats.
- For list endpoints use pagination and provide `meta` in response.
- Provide clear error objects: `{ code, message }`.

## Folder structure responsibilities

- `app/layout` — shell and navigation
- `app/pages` — standalone page components
- `app/services` — API and domain services
- `app/models` — TypeScript interfaces

## Scalability notes

- Consider lazy-loaded feature modules for large sections.
- Add centralized state management (NgRx) when cross-cutting state grows.
- Add telemetry, metrics, and feature flags for controlled rollout.
