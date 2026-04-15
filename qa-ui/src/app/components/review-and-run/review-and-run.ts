import { Component, DestroyRef, inject, ChangeDetectionStrategy, input, effect, signal } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatButtonModule } from '@angular/material/button';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
// import { Loader } from '../../shared/loader/loader';
import { ApiService } from '../../services/api-service/api-service';
import { GenerateTestCasesPayloadResponse, GenerateTestCasesPayload } from '../../shared/models/api.models';

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
  styleUrls: ['./review-and-run.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ReviewAndRun {
  private destroyRef = inject(DestroyRef);

  generationTrigger = input<number>(0);
  private previousTriggerValue = 0;

  /*
   * Reactive signal that holds the generated test cases data.
   * Automatically triggers change detection when updated.
   */
  generatedTestCases = signal<GenerateTestCasesPayloadResponse>({
    runId: '',
    totalTestCount: 0,
    screens: [],
    errors: []
  });

  constructor(private api: ApiService) {
    /*
     * Watch the trigger input and auto-generate test cases (only on change).
     * The effect re-runs whenever generationTrigger changes and compares with previous value.
     */
    effect(() => {
      const currentValue = this.generationTrigger();
      if (currentValue !== this.previousTriggerValue) {
        this.previousTriggerValue = currentValue;
        this.generateTestCases();
      }
    });
  }

 /*
   * Generates test cases by calling the API with the payload.
   * Updates the generatedTestCases signal with the response.
   * The signal automatically triggers change detection and re-renders the UI.
   */
  generateTestCases() {
    const payload: GenerateTestCasesPayload = {
      cacheId: "z8KzX9eaO53rDOb887HYWv",
      screenId: "011",
      testType: "functional",
      testCount: 5,
      prefer_premium: false,
      prdText: "string",
      options: {
        additionalProp1: {}
      },
      generateAll: false
    };

    this.api.generateTestCases(payload)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (response: GenerateTestCasesPayloadResponse) => {
          /* Update the reactive signal with the fetched test cases */
          this.generatedTestCases.set(response);
          console.log('Test cases generated:', response);
        },
        error: err => console.error('Test case generation error:', err)
      });
  }

}