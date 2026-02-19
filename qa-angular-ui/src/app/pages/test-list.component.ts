import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatListModule } from '@angular/material/list';
import { ApiService } from '../services/api.service';

@Component({
  selector: 'app-test-list',
  standalone: true,
  imports: [CommonModule, MatListModule],
  template: `
    <h2>Generated Tests</h2>
    <mat-list>
      <mat-list-item *ngFor="let t of tests">{{t.testId}} — {{t.status}}</mat-list-item>
    </mat-list>
  `
})
export class TestListComponent implements OnInit {
  tests: any[] = [];
  constructor(private api: ApiService) {}
  ngOnInit(): void {
    this.api.get('/tests').subscribe((x: any) => (this.tests = x));
  }
}
