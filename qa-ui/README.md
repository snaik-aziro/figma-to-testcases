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
