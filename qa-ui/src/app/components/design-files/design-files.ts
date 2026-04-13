import {
  Component,
  ContentChild,
  Input,
  TemplateRef,
  ViewChild,
  ElementRef,
  signal,
  effect
} from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatDividerModule } from '@angular/material/divider';
import { MatTooltipModule } from '@angular/material/tooltip';
import { A11yModule } from '@angular/cdk/a11y';

/* Step‑1 panels */
import { DfFigmaPanelComponent } from './df-figma-panel/df-figma-panel';
import { DfJsonPanelComponent } from './df-json-panel.component/df-json-panel.component';

/* Step‑2 & Step‑3 panels */
import { PrdUpload } from '../prd-upload/prd-upload';
import { ReviewAndRun } from '../review-and-run/review-and-run';
import { StorageService } from '../../shared/services/storage-service';
import { ApiService } from '../../services/api-service/api-service';

export interface Steps {
  key: string;
  label: string;
}

type SourceType = 'json' | 'figma';

@Component({
  selector: 'app-design-files',
  standalone: true,
  imports: [
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatDividerModule,
    MatTooltipModule,
    A11yModule,
    DfFigmaPanelComponent,
    DfJsonPanelComponent,
    PrdUpload,
    ReviewAndRun
  ],
  templateUrl: './design-files.html',
  styleUrls: ['./design-files.scss']
})
export class DesignFiles {

  @Input() steps: Steps[] = [
    { key: 'design', label: 'Design Source' },
    { key: 'prd', label: 'PRD Upload' },
    { key: 'review', label: 'Review & Run' },
  ];

  activeIndex = 0;

  get canGoBack(): boolean {
    return this.activeIndex > 0;
  }

  /** We DO NOT use canGoNext for Step‑2 */
  get canGoNext(): boolean {
    return this.activeIndex < this.steps.length - 1;
  }

  @ContentChild('content', { read: TemplateRef })
  contentTpl?: TemplateRef<unknown>;

  /* Step‑1 source toggle */
  source = signal<SourceType>('figma');
  setSource(s: SourceType) {
    this.source.set(s);
  }

  @ViewChild('mainEl') mainEl?: ElementRef<HTMLElement>;
  @ViewChild(PrdUpload) prdUpload!: PrdUpload;

  constructor(
    private api: ApiService,
    private storageService: StorageService
  ) {
    this.getFilesByCacheId();
  }

  /* ---------------- Navigation ---------------- */

  back() {
    if (!this.canGoBack) return;
    this.activeIndex--;
    this.scrollMainToTop();
  }

  gotoStep(i: number) {
    if (i < 0 || i >= this.steps.length) return;
    this.activeIndex = i;
    this.scrollMainToTop();
  }

  private scrollMainToTop() {
    const host = this.mainEl?.nativeElement;
    if (host) host.scrollTo({ top: 0, behavior: 'auto' });
  }

  /* ---------------- Bottom Button Logic ---------------- */

  get primaryButtonLabel(): string {
    if (this.activeIndex === 1) {
      return this.prdUpload?.analysisDone
        ? 'Generate Test Cases'
        : 'Start Analysis';
    }
    return 'Continue';
  }

  onPrimaryClick() {
    if (this.activeIndex !== 1) {
      this.activeIndex++;
      this.scrollMainToTop();
      return;
    }

    if (!this.prdUpload.analysisDone) {
      this.prdUpload.analyze();   // ✅ Start Analysis
      return;
    }

    // ✅ Generate Test Cases
    this.activeIndex++;
    this.prdUpload.generateTestCases();
    this.scrollMainToTop();
  }

  /* ---------------- Keyboard ---------------- */

  onCardKey(event: KeyboardEvent, s: SourceType) {
    const key = event.key?.toLowerCase();
    if (key === 'enter' || key === ' ') {
      event.preventDefault();
      this.setSource(s);
    }
  }

  /* ---------------- JSON Source Side‑Effect ---------------- */

  private jsonApiCalled = false;

  private getFilesByCacheId() {
    effect(() => {
      if (this.source() === 'json' && !this.jsonApiCalled) {
        this.jsonApiCalled = true;

        const cachedId = JSON.parse(
          sessionStorage.getItem('design_files_figma_data') || '{}'
        ).cacheId;

        this.api.getFilesByCacheId(cachedId).subscribe({
          next: res => this.storageService.setDesignFilesJsonData(res),
          error: () => (this.jsonApiCalled = false)
        });
      }
    });
  }
}