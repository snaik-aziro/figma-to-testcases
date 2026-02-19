import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private base = environment.apiBaseUrl.replace(/\/$/, '');
  constructor(private http: HttpClient) {}

  get<T>(path: string, params?: any): Observable<T> {
    const url = `${this.base}${path.startsWith('/') ? path : '/' + path}`;
    return this.http.get<T>(url, { params });
  }

  post<T>(path: string, body: any, headers?: HttpHeaders): Observable<T> {
    const url = `${this.base}${path.startsWith('/') ? path : '/' + path}`;
    return this.http.post<T>(url, body, { headers });
  }

  put<T>(path: string, body: any): Observable<T> {
    const url = `${this.base}${path.startsWith('/') ? path : '/' + path}`;
    return this.http.put<T>(url, body);
  }

  delete<T>(path: string): Observable<T> {
    const url = `${this.base}${path.startsWith('/') ? path : '/' + path}`;
    return this.http.delete<T>(url);
  }
}
