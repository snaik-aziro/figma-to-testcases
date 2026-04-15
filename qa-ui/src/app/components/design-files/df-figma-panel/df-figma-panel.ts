import { Component, DestroyRef, inject, ChangeDetectionStrategy } from '@angular/core';
import { ReactiveFormsModule, FormGroup, FormControl, Validators } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ApiService } from '../../../services/api-service/api-service';
import { StorageService } from '../../../shared/services/storage-service';
import { FigmaFetchPayload, FigmaFetchResponse } from '../../../shared/models/api.models';

@Component({
  selector: 'app-df-figma-panel',
  standalone: true,
  imports: [
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    ReactiveFormsModule
  ],
  templateUrl: './df-figma-panel.html',
  styleUrls: ['./df-figma-panel.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class DfFigmaPanelComponent {
  private destroyRef = inject(DestroyRef);

  figmaForm = new FormGroup({
    fileUrlOrId: new FormControl('', Validators.required),
    token: new FormControl('', Validators.required),
    page: new FormControl('All Pages'),
    cache: new FormControl(true)
  });

  constructor(private api: ApiService,
    private storageService: StorageService
  ) { }

  figmaFetch() {
    if (this.figmaForm.invalid) {
      this.figmaForm.markAllAsTouched();
      return;
    }

    const payload: FigmaFetchPayload = {
      fileUrlOrId: this.figmaForm.value.fileUrlOrId || '',
      token: this.figmaForm.value.token || '',
      options: {
        // page: this.figmaForm.value.page,
        // cache: this.figmaForm.value.cache
      }
    };

    this.api.figmaFetch(payload)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res: FigmaFetchResponse) => {
          console.log('payload sent to API:', payload);
          console.log('Figma fetch response:', res);
          this.storageService.setDesignFilesFigmaData(res);
        },
        error: err => console.error('API error:', err)
      });
  }
}