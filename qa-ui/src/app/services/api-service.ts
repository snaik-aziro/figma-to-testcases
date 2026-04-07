import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs/internal/Observable';

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }


  generateTestCases(payload: any): Observable<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    });

    return this.http.post(
      `${this.baseUrl}/figma/fetch-cache`,
      payload,
      { headers }
    );

  }

  getFilesByCacheId(cacheId: string): Observable<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    });
    return this.http.get(
      `${this.baseUrl}/figma/cache/${cacheId}`,
      { headers }
    );
  }

  analyzeFiles(payload: any): Observable<any> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    });

    return this.http.post(
      `${this.baseUrl}/analyze`,
      payload,
      { headers }
    );

  }
}
