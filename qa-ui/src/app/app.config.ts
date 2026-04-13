import { ApplicationConfig } from '@angular/core';
import {
  provideHttpClient,
  withInterceptorsFromDi
} from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { HTTP_INTERCEPTORS } from '@angular/common/http';

import { routes } from './app.routes';
import { AppHttpInterceptor } from '../app/services/interceptor/http-interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    // ✅ ROUTER PROVIDERS (FIXES ActivatedRoute)
    provideRouter(routes),

    // ✅ HTTP CLIENT + INTERCEPTORS
    provideHttpClient(withInterceptorsFromDi()),

    // ✅ GLOBAL INTERCEPTOR
    {
      provide: HTTP_INTERCEPTORS,
      useClass: AppHttpInterceptor,
      multi: true,
    },
  ],
};