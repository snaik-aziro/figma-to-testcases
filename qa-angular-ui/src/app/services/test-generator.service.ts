import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';

export interface GenerateRequest {
  screenId: string;
  options?: Record<string, unknown>;
}

@Injectable({ providedIn: 'root' })
export class TestGeneratorService {
  constructor(private api: ApiService) {}

  generate(screenId: string, options: Record<string, unknown> = {}): Observable<any> {
    const body: GenerateRequest = { screenId, options };
    return this.api.post('/tests/generate', body);
  }
}
