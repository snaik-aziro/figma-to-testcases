import { Injectable } from '@angular/core';
import {
  HttpInterceptor,
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpErrorResponse
} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, finalize } from 'rxjs/operators';

import { LoaderService } from '../loader-service/loader-service';

@Injectable()
export class AppHttpInterceptor implements HttpInterceptor {

  constructor(
    private loader: LoaderService,
  ) {}

  intercept(
    req: HttpRequest<any>,
    next: HttpHandler
  ): Observable<HttpEvent<any>> {

    // ✅ Add headers globally
    const requestWithHeaders = req.clone({
      setHeaders: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      }
    });

    // ✅ Start loader
    this.loader.show();

    return next.handle(requestWithHeaders).pipe(
      catchError((error: HttpErrorResponse) => {
        console.error('HTTP Error:', error);
        return throwError(() => error);
      }),
      finalize(() => {
        // ✅ Always hide loader (success/error)
        this.loader.hide();
      })
    );
  }
}