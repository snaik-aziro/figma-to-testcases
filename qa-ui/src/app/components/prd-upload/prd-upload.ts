import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-prd-upload',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule
  ],
  templateUrl: './prd-upload.html',
  styleUrl: './prd-upload.scss',
})
export class PrdUpload {

  selectedFile: File | null = null;

  // Summary fields (already used below)
  fileName = '';
  fileSize = '';
  lastModified = '';
  fileType = '';

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;

    this.selectedFile = input.files[0];

    this.fileName = this.selectedFile.name;
    this.fileSize = this.formatFileSize(this.selectedFile.size);
    this.lastModified = new Date(this.selectedFile.lastModified).toLocaleDateString();
    this.fileType = this.selectedFile.type || 'Unknown';

    // ✅ reset so same file can be selected again
    input.value = '';
  }

  private formatFileSize(bytes: number): string {
    if (!bytes) return '0 KB';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  }
}