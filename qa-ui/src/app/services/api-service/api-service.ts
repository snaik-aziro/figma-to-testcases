import { Injectable } from '@angular/core';
import { environment } from '../../../environments/environment';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class ApiService {

  private baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  figmaFetch(payload: any): Observable<any> {
    return this.http.post(
      `${this.baseUrl}/figma/fetch-cache`,
      payload
    );
  }

  getFilesByCacheId(cacheId: string): Observable<any> {
    return this.http.get(
      `${this.baseUrl}/figma/cache/${cacheId}`
    );
  }

  analyzeFiles(payload: any): Observable<any> {
    return this.http.post(
      `${this.baseUrl}/analyze`,
      payload
    );
  }

  generateTestCases(payload: any): Observable<any> {
    return this.http.post(
      `${this.baseUrl}/tests/generate`,
      payload
    );
  }
}
