import { Injectable } from '@angular/core';
const DESIGN_FILES_KEY = 'design_files_figma_data';
const DESIGN_FILES_JSON_KEY = 'design_files_json_data';
@Injectable({
  providedIn: 'root',
})
export class StorageService {

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

  setPrdFileData(data: object): void {
    sessionStorage.setItem(DESIGN_FILES_JSON_KEY, JSON.stringify(data));
  }

  getPrdFileData(): object | null {
    const raw = sessionStorage.getItem(DESIGN_FILES_JSON_KEY);
    return raw ? JSON.parse(raw) : null;
  }

  clearPrdFileData(): void {
    sessionStorage.removeItem(DESIGN_FILES_JSON_KEY);
  }

}
