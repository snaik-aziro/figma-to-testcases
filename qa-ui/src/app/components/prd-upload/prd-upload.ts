import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { StorageService } from '../../shared/services/storage-service';
import { A11yModule } from '@angular/cdk/a11y';
import { ApiService } from '../../services/api-service/api-service';
import { CommonModule } from '@angular/common';

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
  styleUrls: ['./prd-upload.scss'],
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
  selectAllScreens = false;   // ✅ RESTORED

  analysisDone = false;       // ✅ wizard reads this

  constructor(
    private sessionStorage: StorageService,
    private api: ApiService,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit(): void {
    // const stored = this.sessionStorage.getPrdFileData();
    // if (stored) {
    //   this.fileName = stored.name;
    //   this.fileSize = stored.sizeLabel;
    //   this.fileType = stored.type;
    //   this.lastModified = new Date(stored.lastModified).toLocaleDateString();
    //   this.selectedFile = {} as File;
    // }
  }

  // To handle file selection and store file details in session storage
  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files?.length) return;

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

  // Called "Analyze" API to analyze the uploaded PRD file and get screen details
  analyze() {
    //to do replace with realtime data
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

        // ✅ RESET SELECTION STATE FIRST (THIS IS THE FIX)
        this.selectedScreenType = null;
        this.selectedScreenName = null;
        this.selectAllScreens = false;
        this.filteredNames = [];

        this.analysisResponse = screens;

        this.screenTypes = Array.from(
          new Set(
            screens
              .map(s => s.screen_type)
              .filter((t): t is string => typeof t === 'string')
          )
        );

        this.analysisDone = true;
        this.cdr.detectChanges();
      },
      error: err => console.error('Analysis error:', err)
    });
  }

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
      "generateAll": this.selectAllScreens
    }
    this.api.generateTestCases(payload).subscribe({
      next: (response: any) => {
        console.log('Test cases generated:', response);
      },
      error: err => console.error('Test case generation error:', err)
    });
  }

  // To handle screen type selection change
  onScreenTypeChange(event: Event) {
    const type = (event.target as HTMLSelectElement).value;
    this.selectedScreenType = type;
    this.selectAllScreens = false;

    this.filteredNames = this.analysisResponse
      .filter(s => s.screen_type === type)
      .map(s => s.name);

    this.selectedScreenName = null;
  }
  // To handle screen name selection change
  onScreenNameChange(event: Event) {
    this.selectedScreenName = (event.target as HTMLSelectElement).value;
  }

  // To handle "Select All" checkbox change
  onSelectAllChange(checked: boolean) {
    this.selectAllScreens = checked;

    if (checked) {
      this.selectedScreenType = null;
      this.selectedScreenName = null;
      this.filteredNames = [];
    }
  }
}