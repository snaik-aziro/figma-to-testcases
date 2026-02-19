import { Routes } from '@angular/router';
import { DashboardComponent } from './pages/dashboard.component';
import { GenerateTestComponent } from './pages/generate-test.component';
import { TestListComponent } from './pages/test-list.component';
import { SettingsComponent } from './pages/settings.component';

export const routes: Routes = [
  { path: '', component: DashboardComponent },
  { path: 'generate', component: GenerateTestComponent },
  { path: 'tests', component: TestListComponent },
  { path: 'settings', component: SettingsComponent },
  { path: '**', redirectTo: '' }
];
