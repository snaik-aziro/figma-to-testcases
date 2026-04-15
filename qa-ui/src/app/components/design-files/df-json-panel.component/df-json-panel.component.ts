import { Component, ChangeDetectionStrategy, signal, inject, DestroyRef } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { StorageService } from '../../../shared/services/storage-service';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { CommonModule } from '@angular/common';

@Component({
  imports: [MatCardModule, MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule,
    MatSelectModule, CommonModule
  ],
  selector: 'app-df-json-panel',
  templateUrl: './df-json-panel.component.html',
  styleUrls: ['./df-json-panel.component.scss'],
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
})

export class DfJsonPanelComponent {

  /*
   * Signal that holds the list of cached design files retrieved from storage.
   * This signal is reactive and automatically triggers change detection when updated.
   */
  cachedFiles = signal<any[]>([]);

  private destroyRef = inject(DestroyRef);

  constructor(private storageService: StorageService) {
    /* Initialize by loading cached files from storage when the component is created */
    this.loadCachedFiles();
  }

  /*
   * Private method to load cached design files from the storage service.
   * 
   * Process:
   * 1. Retrieve the stored design files from the storage service
   * 2. Normalize the data (convert single objects to arrays if needed)
   * 3. Update the cachedFiles signal with the normalized data
   * 4. If no data exists, set an empty array
   */
  private loadCachedFiles() {
    /* Fetch the cached design files from storage */
    const stored = this.storageService.getDesignFilesJsonData();

    /*
     * Normalize the data: ensure cachedFiles is always an array.
     * If stored data is not an array, wrap it in one; if null/undefined, use empty array.
     */
    this.cachedFiles.set(stored ? (Array.isArray(stored) ? stored : [stored]) : []);
  }

  /*
   * Public refresh method that reloads the cached files from storage.
   * Called by the parent component when new data becomes available.
   * Ensures the UI displays the most current cached files.
   */
  refresh(): void {
    this.loadCachedFiles();
  }

  /*
   * Handles the selection event when a user chooses a cached design file from the dropdown.
   * 
   * Process:
   * 1. Extract the selected index from the dropdown event
   * 2. Validate that the index is a valid number
   * 3. Retrieve the design file at that index
   * 4. Update the storage service with the selected file
   */
  onCachedIndexSelect(event: Event): void {
    /* Extract the selected index from the HTML select element */
    const selectedIndex = +(event.target as HTMLSelectElement).value;

    /* Validate: exit early if index is not a valid number */
    if (isNaN(selectedIndex)) return;

    /* Retrieve the design file object at the selected index */
    const selectedFile = this.cachedFiles()[selectedIndex];

    /*
     * Update the storage service with the newly selected design file.
     * This allows other components to access and work with this file.
     */
    this.storageService.setDesignFilesJsonData(selectedFile);
  }
}
