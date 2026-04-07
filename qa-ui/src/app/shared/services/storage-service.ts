import { Injectable } from '@angular/core';
const DESIGN_FILES_KEY = 'design_files_figma_data';
const DESIGN_FILES_JSON_KEY = 'design_files_json_data';
const PRD_FILE = 'prd_file_data';
export interface PrdFileData {
  name: string;
  size: number;
  sizeLabel: string;
  type: string;
  lastModified: number;
}

@Injectable({
  providedIn: 'root',
})
export class StorageService {
  // To store the data related to the design files fetched from Figma API, Step 1 of the flow.
  setDesignFilesFigmaData(data: object): void {
    sessionStorage.setItem(DESIGN_FILES_KEY, JSON.stringify(data));
  }

  getDesignFilesFigmaData(): object | null {
    const raw = sessionStorage.getItem(DESIGN_FILES_KEY);
    return raw ? JSON.parse(raw) : null;
  }

  clearDesignFilesFigmaData(): void {
    sessionStorage.removeItem(DESIGN_FILES_KEY);
  }

  // To store the data related to the design files in JSON format, Step 1 of the flow.
  setDesignFilesJsonData(data: object): void {
    sessionStorage.setItem(DESIGN_FILES_JSON_KEY, JSON.stringify(data));
  }

  getDesignFilesJsonData(): object | null {
    const raw = sessionStorage.getItem(DESIGN_FILES_JSON_KEY);
    return raw ? JSON.parse(raw) : null;
  }

  clearDesignFilesJsonData(): void {
    sessionStorage.removeItem(DESIGN_FILES_JSON_KEY);
  }

  // To store the data related to the PRD file, Step 2 of the flow.

  setPrdFileData(data: PrdFileData): void {
    sessionStorage.setItem(PRD_FILE, JSON.stringify(data));
  }

  getPrdFileData(): PrdFileData | null {
    const raw = sessionStorage.getItem(PRD_FILE);
    return raw ? (JSON.parse(raw) as PrdFileData) : null;
  }

  clearPrdFileData(): void {
    sessionStorage.removeItem(PRD_FILE);
  }

}
