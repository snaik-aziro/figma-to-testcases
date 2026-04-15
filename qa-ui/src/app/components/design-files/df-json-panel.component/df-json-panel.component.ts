import { Component, ChangeDetectionStrategy, signal, effect, inject, DestroyRef } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { StorageService } from '../../../shared/services/storage-service';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-df-json-panel',
  standalone: true,
  imports: [MatCardModule, MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule,
    MatSelectModule, CommonModule
  ],
  templateUrl: './df-json-panel.component.html',
  styleUrls: ['./df-json-panel.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class DfJsonPanelComponent {
  cachedFiles = signal<any[]>([]);
  private destroyRef = inject(DestroyRef);

  constructor(private storageService: StorageService) {
    this.loadCachedFiles();
  }

  private loadCachedFiles() {
    // ✅ Load cached files when component initializes
    const stored = this.storageService.getDesignFilesJsonData();
    this.cachedFiles.set(stored ? (Array.isArray(stored) ? stored : [stored]) : []);
  }

  // ✅ Public refresh method called by parent when data is updated
  refresh(): void {
    this.loadCachedFiles();
  }

  onCachedIndexSelect(event: Event): void {
    const selectedIndex = +(event.target as HTMLSelectElement).value;

    if (isNaN(selectedIndex)) return;

    const selectedFile = this.cachedFiles()[selectedIndex];

    this.storageService.setDesignFilesJsonData(selectedFile);
    console.log('Selected cached design:', selectedFile);
  }
}
