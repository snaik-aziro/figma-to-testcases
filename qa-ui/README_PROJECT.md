# QA Test Generator Angular UI — Project README

This file includes architecture, UI→API mapping table, payload examples, run instructions, environment configuration and alignment notes.

## ASCII High-level Architecture

Browser (User) -> Angular UI (Standalone components + Angular Material) -> REST API (Backend)

Components:
- App Shell (`AppComponent`): Topbar, Sidebar, Content area (router outlet)
- Pages: Dashboard, Generate Test, Test List, Settings
- Services: `ApiService` (generic), `TestGeneratorService` (domain)
- Interceptor: `AuthInterceptor` (placeholder)

## UI-to-API mapping

| UI Component | User Action | API Endpoint | Method | Request Body | Response |
|--------------|-------------|--------------|--------|--------------|----------|
| GenerateTestComponent | Submit generate request | /api/tests/generate | POST | { screenId, options } | { testId, status, tests } |
| TestListComponent | Fetch all tests | /api/tests | GET | — | [ { testId, name, status } ] |
| DashboardComponent | Get summary | /api/dashboard/summary | GET | — | { activeJobs, lastRun } |
| Sidebar | Get screens | /api/screens | GET | — | [ { screenId, name } ] |

## Example API JSONs

Generate request:

```json
{
  "screenId": "screen_123",
  "options": { "depth": "medium", "includeEdgeCases": true }
}
```

Generate response:

```json
{
  "testId": "tst_789",
  "status": "queued",
  "tests": []
}
```

## How to run locally

1. Install dependencies: `npm install`
2. Start dev server: `npm run start`
3. Open `http://localhost:4200`

Note: `environment.ts` points at `http://localhost:8000/api` by default. Adjust if backend runs at different host/port.

## Environment configuration

Files:
- `src/environments/environment.ts` - development
- `src/environments/environment.prod.ts` - production

Set `apiBaseUrl` to your backend root, e.g. `https://api.internal.company.example/api`.

## Backend alignment

- Endpoints should live under the configured `apiBaseUrl`.
- Use consistent JSON shapes and provide pagination for list endpoints.
- Provide detailed error objects: `{ code, message }`.

## Folder responsibilities

- `app/layout` - composable layout components
- `app/pages` - standalone pages
- `app/services` - Http services, domain services, and interceptors
- `app/models` - typed interfaces

## Scalability notes

- Convert large pages to lazy-loaded modules.
- Add centralized state management (NgRx, signals) when needed.
- Add feature flags and telemetry for staged rollout.
