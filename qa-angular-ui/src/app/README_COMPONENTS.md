This folder contains standalone components used across the application:

- `TopbarComponent` — top navigation bar
- `SidebarComponent` — side navigation
- `DashboardComponent` — summary view
- `GenerateTestComponent` — test generation UI
- `TestListComponent` — lists generated tests

Each component is implemented as a standalone component (no NgModule), imports only necessary Angular and Angular Material pieces, and is intended to be small and testable.
