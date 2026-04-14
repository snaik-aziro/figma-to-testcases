import { Component } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatButtonModule } from '@angular/material/button';
// import { Loader } from '../../shared/loader/loader';
import { ApiService } from '../../services/api-service/api-service';
import { GeneratedTestCasesResponse } from '../../shared/models/test-case.model';

@Component({
  selector: 'app-review-and-run',
  standalone: true,
  imports: [
    MatIconModule,
    MatCardModule,
    MatExpansionModule,
    MatButtonModule,
    // Loader
  ],
  templateUrl: './review-and-run.html',
  styleUrls: ['./review-and-run.scss']
})
export class ReviewAndRun {
constructor(private api: ApiService) { }

  generatedTestCases: GeneratedTestCasesResponse = {
    runId: '',
    totalTestCount: 0,
    screens: [],
    errors: []
  };

 // Called "Generate Test Cases" API based on selected screen or "Select All" option
  generateTestCases() {
    const payload = {
      cacheId: "z8KzX9eaO53rDOb887HYWv",
      screenId: "011",
      testType: "functional",
      testCount: 5,
      prefer_premium: false,
      prdText: "string",
      options: {
        additionalProp1: {}
      },
      "generateAll": false
    }
    this.api.generateTestCases(payload).subscribe({
      next: (response: any) => {
        this.generatedTestCases = response;
        console.log('Test cases generated:', response);
      },
      error: err => console.error('Test case generation error:', err)
    });
  }

}