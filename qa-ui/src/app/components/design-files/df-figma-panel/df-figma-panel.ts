import { Component, DestroyRef, inject, ChangeDetectionStrategy } from '@angular/core';
import { ReactiveFormsModule, FormGroup, FormControl, Validators } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ApiService } from '../../../services/api-service/api-service';
import { StorageService } from '../../../shared/services/storage-service';
import { FigmaFetchPayload, FigmaFetchResponse } from '../../../shared/models/api.models';

@Component({
  imports: [
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    ReactiveFormsModule
  ],
  selector: 'app-df-figma-panel',
  templateUrl: './df-figma-panel.html',
  styleUrls: ['./df-figma-panel.scss'],
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush
})

export class DfFigmaPanelComponent {
  private destroyRef = inject(DestroyRef);

  /*
   * Reactive form for collecting Figma authentication and file details from the user.
   * 
   * Fields:
   * - fileUrlOrId: The Figma file URL or file ID to fetch designs from (required)
   * - token: Figma personal access token for API authentication (required)
   * - page: Which page(s) to fetch from the file (reserved for future use)
   * - cache: Whether to cache the fetched results for faster subsequent access
   */
  figmaForm = new FormGroup({
    fileUrlOrId: new FormControl('', Validators.required),
    token: new FormControl('', Validators.required),
    page: new FormControl('All Pages'),
    cache: new FormControl(true)
  });

  constructor(private api: ApiService,
    private storageService: StorageService
  ) { }

  /*
   * Fetches design files from Figma API based on form inputs.
   * 
   * Process Flow:
   * 1. Validates the form (fileUrlOrId and token are required)
   * 2. If invalid, marks all fields as touched to show validation errors to the user
   * 3. If valid, constructs the API request payload with user-provided credentials
   * 4. Sends the payload to the backend API to fetch Figma designs
   */
  figmaFetch() {
    if (this.figmaForm.invalid) {
      /* Mark all form fields as touched to trigger validation error displays in the UI */
      this.figmaForm.markAllAsTouched();
      return;
    }

    /*
     * Prepare the request payload containing the Figma credentials and configuration.
     * The backend will use these details to authenticate with Figma and retrieve the design file.
     */
    const payload: FigmaFetchPayload = {
      fileUrlOrId: this.figmaForm.value.fileUrlOrId || '',
      token: this.figmaForm.value.token || '',
      options: {
        /* Note: page and cache options are commented out but available for future implementation */
        // page: this.figmaForm.value.page,
        // cache: this.figmaForm.value.cache
      }
    };

    /*
     * Send the payload to the backend API to fetch designs from Figma.
     * The API will use the provided access token to authenticate and retrieve the design file.
     * Subscription is automatically cleaned up when the component is destroyed (takeUntilDestroyed).
     */
    this.api.figmaFetch(payload)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res: FigmaFetchResponse) => {
          /*
           * Store the fetched Figma design data in the storage service.
           * This makes the design data accessible to other components in the application.
           */
          this.storageService.setDesignFilesFigmaData(res);
        },
        error: (err) => {
          /* Error: Log any API or network errors encountered during the fetch request */
          console.error('API error:', err);
        }
      });
  }
}