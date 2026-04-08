import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { A11yModule } from '@angular/cdk/a11y';
import { ApiService } from '../../services/api-service';
import { StorageService } from '../../shared/services/storage-service';

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
  styleUrls: ['./prd-upload.scss']
})
export class PrdUpload implements OnInit {

  selectedFile: File | null = null;
  fileName = '';
  fileSize = '';
  fileType = '';
  lastModified = '';

  analysisResponse: ScreenItem[] = [];
  screenTypes: string[] = [];
  filteredNames: string[] = [];

  selectedScreenType: string | null = null;
  selectedScreenName: string | null = null;

  /** ✅ Wizard reads ONLY this */
  analysisDone = false;

  constructor(
    private storage: StorageService,
    private api: ApiService
  ) { }

  ngOnInit(): void {
    const stored = this.storage.getPrdFileData();
    if (stored) {
      this.fileName = stored.name;
      this.fileSize = stored.sizeLabel;
      this.fileType = stored.type;
      this.lastModified = new Date(stored.lastModified).toLocaleDateString();
      this.selectedFile = {} as File;
    }
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files?.length) return;

    const file = input.files[0];
    this.selectedFile = file;

    this.fileName = file.name;
    this.fileSize = `${(file.size / 1024).toFixed(1)} KB`;
    this.fileType = file.type || 'Unknown';
    this.lastModified = new Date(file.lastModified).toLocaleDateString();

    this.storage.setPrdFileData({
      name: file.name,
      size: file.size,
      sizeLabel: this.fileSize,
      type: this.fileType,
      lastModified: file.lastModified
    });

    input.value = '';
  }

  analyze() {
    const payload = {
      cacheId: 'z8KzX9eaO53rDOb887HYWv',
      prdText: 'Users can sign in using email and password...',
      options: { applyFiltering: true }
    };

    this.api.analyzeFiles(payload).subscribe({
      next: (res: any) => {
        const screens: ScreenItem[] = Array.isArray(res?.screens)
          ? res.screens
          : [];

        this.analysisResponse = screens;
        this.screenTypes = Array.from(
          new Set(
            screens
              .map(s => s.screen_type)
              .filter((t): t is string => typeof t === 'string')
          )
        );

        this.analysisDone = true;   // ✅ button changes here
      },
      error: err => console.error(err)
    });
  }

  onScreenTypeChange(event: Event) {
    const type = (event.target as HTMLSelectElement).value;
    this.selectedScreenType = type;
    this.filteredNames = this.analysisResponse
      .filter(s => s.screen_type === type)
      .map(s => s.name);
  }

  onScreenNameChange(event: Event) {
    this.selectedScreenName = (event.target as HTMLSelectElement).value;
  }
}