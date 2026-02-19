import { Injectable } from '@angular/core';
import { HttpEvent, HttpHandler, HttpInterceptor, HttpRequest } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AuthInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Placeholder for adding auth token when authentication is implemented.
    // Example:
    // const token = authService.getToken();
    // if (token) { req = req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }); }
    return next.handle(req);
  }
}
