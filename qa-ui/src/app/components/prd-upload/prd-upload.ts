import { Component, OnInit, ChangeDetectorRef, DestroyRef, inject, ChangeDetectionStrategy } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { StorageService } from '../../shared/services/storage-service';
import { A11yModule } from '@angular/cdk/a11y';
import { ApiService } from '../../services/api-service/api-service';
import { CommonModule } from '@angular/common';
import { AnalyzeFilesPayload, AnalyzeFilesResponse, DesignFilesResponse, ScreenItem } from '../../shared/models/api.models';

@Component({
  selector: 'app-prd-upload',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    A11yModule
  ],
  templateUrl: './prd-upload.html',
  styleUrls: ['./prd-upload.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})

export class PrdUpload {
  private destroyRef = inject(DestroyRef);

  /* ==================== File Upload Section ==================== */

  /*
   * Stores the selected PRD file object.
   * Set when user chooses a file via the file input element.
   */
  selectedFile: File | null = null;

  /* Display information about the selected file */
  fileName = '';        // File name with extension (e.g., "requirements.pdf")
  fileSize = '';        // Human-readable file size (e.g., "2.5 MB")
  lastModified = '';    // Formatted last modified date
  fileType = '';        // MIME type of the file

  /* ==================== Analysis Section ==================== */

  /*
   * Array of screen items extracted from the PRD analysis.
   * Contains screens with their types, names, and descriptions.
   */
  analysisResponse: ScreenItem[] = [];

  /* Unique screen types extracted from the analysis response (e.g., ["Login", "Dashboard", "Settings"]) */
  screenTypes: string[] = [];

  /* Screen names filtered by the selected screen type (e.g., ["Login Screen", "Login with Email"]) */
  filteredNames: string[] = [];

  /* Currently selected screen type from the dropdown */
  selectedScreenType: string | null = null;

  /* Currently selected screen name from the dropdown */
  selectedScreenName: string | null = null;

  /* Flag indicating whether user wants to select all screens or specific ones */
  selectAllScreens = false;

  /* Flag indicating whether the PRD analysis has been completed successfully */
  analysisDone = false;

  /* Specifies the cache ID to use for API calls */
  cacheId: string = '';

  constructor(
    private sessionStorage: StorageService,
    private api: ApiService,
    private cdr: ChangeDetectorRef
  ) { }

  /* ==================== File Upload Handlers ==================== */

  /*
   * Handles file selection event when user picks a PRD file.
   * 
   * Process:
   * 1. Extract the file from the input element
   * 2. Store file reference and calculate metadata (name, size, type, date)
   * 3. Save file metadata to session storage for persistence
   * 4. Clear the input value to allow selecting the same file again
   */
  onFileSelected(event: Event) {
    /* Get the file input element and extract the selected file */
    const input = event.target as HTMLInputElement;
    if (!input.files?.length) return;

    const file = input.files[0];
    this.selectedFile = file;

    /* Extract and format file metadata for display */
    this.fileName = file.name;
    this.fileSize = this.formatFileSize(file.size);
    this.lastModified = new Date(file.lastModified).toLocaleDateString();
    this.fileType = file.type || 'Unknown';

    /*
     * Persist file metadata to session storage.
     * This allows the metadata to be recovered if the page is refreshed.
     */
    this.sessionStorage.setPrdFileData({
      name: file.name,
      size: file.size,
      sizeLabel: this.fileSize,
      type: this.fileType,
      lastModified: file.lastModified
    });

    /* Clear the input value to allow selecting the same file again */
    input.value = '';
  }

  /*
   * Converts file size in bytes to human-readable format (Bytes, KB, MB, GB).
   * Example: 2621440 bytes → "2.5 MB"
   */
  private formatFileSize(bytes: number): string {
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  }

  /* ==================== Analysis API ==================== */

  /*
   * Calls the backend API to analyze the uploaded PRD file.
   * 
   * Process:
   * 1. Prepare the analysis request payload with cache ID and PRD text
   * 2. Send request to the API
   * 3. Extract screen data from the response
   * 4. Reset selection state to clear previous selections
   * 5. Build list of unique screen types for filtering
   * 6. Mark analysis as complete
   * 7. Trigger change detection to update the UI
   */
  analyze() {
    const payload: AnalyzeFilesPayload = {
      cacheId: this.sessionStorage.cacheId,
      prdText: 'Users can sign in using email and password...',
      options: { applyFiltering: true }
    };

    /*
     * Send the analysis request to the API.
     * Subscription is automatically cleaned up when component is destroyed.
     */
    this.api.analyzeFiles(payload)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (response: AnalyzeFilesResponse) => {
          /* Extract screens array from response, defaulting to empty array if invalid */
          const screens: ScreenItem[] = Array.isArray(response?.screens)
            ? response.screens
            : [];

          /*
           * Reset all selection state BEFORE processing new analysis results.
           * This prevents stale selections from affecting the new data.
           */
          this.selectedScreenType = null;
          this.selectedScreenName = null;
          this.selectAllScreens = false;
          this.filteredNames = [];

          /* Store the analysis response (all screens) */
          this.analysisResponse = screens;

          /*
           * Extract unique screen types from the analysis response.
           * Used to populate the screen type dropdown filter.
           * Example: ["Login Screen", "Dashboard", "Settings"]
           */
          this.screenTypes = Array.from(
            new Set(
              screens
                .map(s => s.screen_type)
                .filter((t): t is string => typeof t === 'string')
            )
          );

          /* Mark analysis as complete - wizard can now enable the next step button */
          this.analysisDone = true;

          /* Manually trigger change detection due to OnPush strategy */
          this.cdr.detectChanges();
        },
        error: err => console.error('Analysis error:', err)
      });
  }

  /* ==================== Screen Selection Handlers ==================== */

  /*
   * Handles screen type selection change from the dropdown.
   * Filters available screen names based on the selected type.
   * 
   * Process:
   * 1. Store the selected screen type
   * 2. Reset "Select All" flag (user is making a specific selection)
   * 3. Filter screen names that match this type
   * 4. Reset screen name selection to allow user to choose from new filtered list
   */
  onScreenTypeChange(event: Event) {
    /* Extract the selected screen type from the dropdown */
    const type = (event.target as HTMLSelectElement).value;
    this.selectedScreenType = type;

    /* User is making a specific selection, not selecting all */
    this.selectAllScreens = false;

    /* Filter the list of screen names to only show screens of this type */
    this.filteredNames = this.analysisResponse
      .filter(s => s.screen_type === type)
      .map(s => s.name);

    /* Reset screen name selection since the filtered list has changed */
    this.selectedScreenName = null;
  }

  /*
   * Handles screen name selection change from the dropdown.
   * Updates the selectedScreenName property with the user's choice.
   */
  onScreenNameChange(event: Event) {
    this.selectedScreenName = (event.target as HTMLSelectElement).value;
  }

  /*
   * Handles "Select All Screens" checkbox change.
   * When checked, clears all specific selections (type and name).
   * When unchecked, lets user make specific selections again.
   */
  onSelectAllChange(checked: boolean) {
    this.selectAllScreens = checked;

    if (checked) {
      /* Clear specific selections when "Select All" is checked */
      this.selectedScreenType = null;
      this.selectedScreenName = null;
      this.filteredNames = [];
    }
  }
}