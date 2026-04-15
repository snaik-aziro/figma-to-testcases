import { Injectable } from '@angular/core';
import { environment } from '../../../environments/environment';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  FigmaFetchPayload,
  FigmaFetchResponse,
  DesignFilesResponse,
  AnalyzeFilesPayload,
  AnalyzeFilesResponse,
  GenerateTestCasesPayload,
  GenerateTestCasesPayloadResponse
} from '../../shared/models/api.models';

@Injectable({
  providedIn: 'root',
})
export class ApiService {

  private baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  figmaFetch(payload: FigmaFetchPayload): Observable<FigmaFetchResponse> {
    return this.http.post<FigmaFetchResponse>(
      `${this.baseUrl}/figma/fetch-cache`,
      payload
    );
  }

  getFilesByCacheId(cacheId: string): Observable<DesignFilesResponse> {
    return this.http.get<DesignFilesResponse>(
      `${this.baseUrl}/figma/cache/${cacheId}`
    );
  }

  analyzeFiles(payload: AnalyzeFilesPayload): Observable<AnalyzeFilesResponse> {
    return this.http.post<AnalyzeFilesResponse>(
      `${this.baseUrl}/analyze`,
      payload
    );
  }

  generateTestCases(payload: GenerateTestCasesPayload): Observable<GenerateTestCasesPayloadResponse> {
    return this.http.post<GenerateTestCasesPayloadResponse>(
      `${this.baseUrl}/tests/generate`,
      payload
    );
  }
}
