import { Injectable } from '@angular/core';
const DESIGN_FILES_KEY = 'design_files_data';
@Injectable({
  providedIn: 'root',
})
export class StorageService {

  setDesignFilesData(data: object): void {
    sessionStorage.setItem(DESIGN_FILES_KEY, JSON.stringify(data));
  }

  getDesignFilesData(): object | null {
    const raw = sessionStorage.getItem(DESIGN_FILES_KEY);
    return raw ? JSON.parse(raw) : null;
  }

  clearDesignFilesData(): void {
    sessionStorage.removeItem(DESIGN_FILES_KEY);
  }

}
