import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule, MatListModule, MatIconModule],
  template: `
    <mat-nav-list>
      <a mat-list-item routerLink="/">
        <mat-icon>dashboard</mat-icon>
        <span>Dashboard</span>
      </a>
      <a mat-list-item routerLink="/generate">
        <mat-icon>play_circle</mat-icon>
        <span>Generate Test</span>
      </a>
      <a mat-list-item routerLink="/tests">
        <mat-icon>list</mat-icon>
        <span>Tests</span>
      </a>
      <a mat-list-item routerLink="/settings">
        <mat-icon>settings</mat-icon>
        <span>Settings</span>
      </a>
    </mat-nav-list>
  `
})
export class SidebarComponent {}
