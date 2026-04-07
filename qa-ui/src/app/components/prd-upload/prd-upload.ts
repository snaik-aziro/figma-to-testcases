import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { StorageService } from '../../shared/services/storage-service';
import { A11yModule } from '@angular/cdk/a11y';
import { ApiService } from '../../services/api-service';

interface ScreenItem {
  name: string;
  screen_type: string;
}

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
  styleUrl: './prd-upload.scss',
})
export class PrdUpload implements OnInit {

  /* ---------- File Upload ---------- */
  selectedFile: File | null = null;
  fileName = '';
  fileSize = '';
  lastModified = '';
  fileType = '';

  /* ---------- Analysis ---------- */
  analysisResponse: ScreenItem[] = [];
  screenTypes: string[] = [];
  filteredNames: string[] = [];

  selectedScreenType: string | null = null;
  selectedScreenName: string | null = null;

  constructor(
    private sessionStorage: StorageService,
    private api: ApiService
  ) {}

  /* ✅ RESTORE DATA ON PAGE LOAD */
  ngOnInit(): void {
    const stored = this.sessionStorage.getPrdFileData();
    console.log('Restoring file data from session storage:', stored);
    if (stored) {
      this.fileName = stored?.name;
      this.fileSize = stored?.sizeLabel;
      this.fileType = stored?.type;
      this.lastModified = new Date(stored?.lastModified).toLocaleDateString();

      /**
       * ✅ IMPORTANT:
       * We don't have the actual File object after refresh.
       * But we only need selectedFile truthy to show summary.
       */
      this.selectedFile = {} as File;
    }
  }

  /* ✅ File upload handler */
  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;

    const file = input.files[0];
    this.selectedFile = file;

    this.fileName = file.name;
    this.fileSize = this.formatFileSize(file.size);
    this.lastModified = new Date(file.lastModified).toLocaleDateString();
    this.fileType = file.type || 'Unknown';

    this.sessionStorage.setPrdFileData({
      name: file.name,
      size: file.size,
      sizeLabel: this.fileSize,
      type: this.fileType,
      lastModified: file.lastModified
    });

    input.value = '';
  }

  private formatFileSize(bytes: number): string {
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  }

  analyze() {
    const payload = {
      cacheId: 'z8KzX9eaO53rDOb887HYWv',
      prdText: 'Users can sign in using email and password...',
      options: { applyFiltering: true }
    };

    this.api.analyzeFiles(payload).subscribe({
      next: (response: any) => {
        const screens: ScreenItem[] = Array.isArray(response?.screens)
          ? response.screens
          : [];

        this.analysisResponse = screens;

        this.screenTypes = Array.from(
          new Set(
            screens
              .map(s => s.screen_type)
              .filter(Boolean)
          )
        );

        this.selectedScreenType = null;
        this.selectedScreenName = null;
        this.filteredNames = [];
      },
      error: err => console.error('Analysis error:', err)
    });
  }

  onScreenTypeChange(event: Event) {
    const select = event.target as HTMLSelectElement;
    const type = select.value;

    this.selectedScreenType = type;

    this.filteredNames = this.analysisResponse
      .filter(s => s.screen_type === type)
      .map(s => s.name);

    this.selectedScreenName = null;
  }

  onScreenNameChange(event: Event) {
    const select = event.target as HTMLSelectElement;
    this.selectedScreenName = select.value;
  }
}