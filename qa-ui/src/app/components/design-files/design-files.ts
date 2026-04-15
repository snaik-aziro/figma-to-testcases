import {
  Component,
  ContentChild,
  Input,
  TemplateRef,
  ViewChild,
  ElementRef,
  signal,
  effect,
  ChangeDetectorRef,
  DestroyRef,
  inject,
  ChangeDetectionStrategy
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
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
import { Steps, SourceType } from '../../shared/models/design-files.model';

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
  styleUrls: ['./design-files.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
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
  generateTestCasesTrigger = signal(0);  // ✅ Signal to trigger test case generation

  setSource(s: SourceType) {
    this.source.set(s);
    // ✅ When switching to JSON, fetch the files
    if (s === 'json' && !this.hasLoadedJsonFiles) {
      this.loadJsonFiles();
    }
  }

  @ViewChild('mainEl') mainEl?: ElementRef<HTMLElement>;
  @ViewChild(PrdUpload) prdUpload?: PrdUpload;
  @ViewChild(ReviewAndRun) reviewAndRun?: ReviewAndRun;
  @ViewChild(DfJsonPanelComponent) jsonPanel?: DfJsonPanelComponent;

  private destroyRef = inject(DestroyRef);
  private hasLoadedJsonFiles = false;

  constructor(
    private api: ApiService,
    private storageService: StorageService,
    private cdr: ChangeDetectorRef
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

    if (!this.prdUpload?.analysisDone) {
      this.prdUpload?.analyze();   // ✅ Start Analysis
      return;
    }

    // ✅ Generate Test Cases
    this.activeIndex++;
    this.cdr.detectChanges();
    this.generateTestCasesTrigger.update(v => v + 1);  // ✅ Trigger generation via signal
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

  /* ---------------- JSON Files Loading  ---------------- */

  private loadJsonFiles() {
    const cachedIdStr = sessionStorage.getItem('design_files_figma_data');
    
    if (!cachedIdStr) {
      console.warn('No cached figma data found in sessionStorage');
      return;
    }

    try {
      const cachedData = JSON.parse(cachedIdStr);
      const cachedId = cachedData?.cacheId;

      if (!cachedId) {
        console.warn('Cache ID is missing from sessionStorage');
        return;
      }

      this.hasLoadedJsonFiles = true; // ✅ Mark as loaded BEFORE API call to prevent re-runs
      
      this.api.getFilesByCacheId(cachedId)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: (res) => {
            this.storageService.setDesignFilesJsonData(res);
            // ✅ Notify JSON panel to refresh
            this.jsonPanel?.refresh();
            console.log('JSON files loaded successfully');
          },
          error: (err) => {
            console.error('Failed to load JSON files:', err);
            this.hasLoadedJsonFiles = false; // ✅ Reset on error to allow retry
          }
        });
    } catch (e) {
      console.error('Error parsing cached data:', e);
    }
  }

  private getFilesByCacheId() {
    // ✅ Keep effect only to track source changes (no signal dependency issues)
    effect(() => {
      // This effect just watches the source signal
      // Actual loading is triggered by setSource()
      this.source();
    });
  }
}