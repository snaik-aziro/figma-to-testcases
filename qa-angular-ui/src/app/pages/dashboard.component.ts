import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { ApiService } from '../services/api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, MatCardModule],
  template: `
    <h2>Dashboard</h2>
    <mat-card>
      <p *ngIf="summary">Active Jobs: {{summary.activeJobs}}</p>
      <p *ngIf="summary">Last Run: {{summary.lastRun}}</p>
    </mat-card>
  `
})
export class DashboardComponent implements OnInit {
  summary: any;
  constructor(private api: ApiService) {}
  ngOnInit(): void {
    this.api.get('/dashboard/summary').subscribe(x => (this.summary = x));
  }
}
