import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule],
  template: `
    <h2>Settings</h2>
    <p>Placeholder for settings and auth configuration.</p>
  `
})
export class SettingsComponent {}
