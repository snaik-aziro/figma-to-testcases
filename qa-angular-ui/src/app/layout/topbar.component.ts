import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-topbar',
  standalone: true,
  imports: [CommonModule, MatToolbarModule, MatIconModule],
  template: `
    <mat-toolbar color="primary">
      <span class="mat-headline">QA Test Generator</span>
      <span style="flex:1 1 auto"></span>
      <button mat-icon-button aria-label="Settings">
        <mat-icon>settings</mat-icon>
      </button>
    </mat-toolbar>
  `
})
export class TopbarComponent {}
