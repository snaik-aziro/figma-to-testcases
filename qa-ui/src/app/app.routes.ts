import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'dashboard' },

  {
    path: 'dashboard',
    loadComponent: () =>
      import('./components/dashboard/dashboard').then(m => m.Dashboard)
  },
  {
    path: 'design-files',
    loadComponent: () =>
      import('./components/design-files/design-files').then(m => m.DesignFiles)
  },
  {
    path: 'prd',
    loadComponent: () =>
      import('./components/prd-upload/prd-upload').then(m => m.PrdUpload)
  },
  {
    path: 'review',
    loadComponent: () =>
      import('./components/review-and-run/review-and-run').then(m => m.ReviewAndRun)
  },
];
