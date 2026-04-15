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
/*
 * Main wizard component that manages the multi-step workflow for design file management and test case generation.
 * 
 * Three-step workflow:
 * Step 1 (Design Source): User selects and loads design files (from Figma API or cached JSON files)
 * Step 2 (PRD Upload): User uploads PRD documents for analysis
 * Step 3 (Review & Run): Review and generate test cases based on designs and PRD
 * 
 * Uses reactive signals for state management and inter-component communication.
 */
export class DesignFiles {

  /*
   * Input array defining the steps in the wizard workflow.
   * Each step has a unique key and a user-friendly label.
   */
  @Input() steps: Steps[] = [
    { key: 'design', label: 'Design Source' },
    { key: 'prd', label: 'PRD Upload' },
    { key: 'review', label: 'Review & Run' },
  ];

  /* Tracks the currently active step index (0 = Design Source, 1 = PRD Upload, 2 = Review & Run) */
  activeIndex = 0;

  /*
   * Determines if the user can navigate backward to the previous step.
   * Returns false if already at the first step.
   */
  get canGoBack(): boolean {
    return this.activeIndex > 0;
  }

  /*
   * Determines if the user can navigate forward to the next step.
   * Note: Not used for Step 2 (PRD Upload) as user must complete analysis first.
   */
  get canGoNext(): boolean {
    return this.activeIndex < this.steps.length - 1;
  }

  @ContentChild('content', { read: TemplateRef })
  contentTpl?: TemplateRef<unknown>;

  /*
   * Signal that tracks which design source is selected by the user.
   * Toggles between 'figma' (API) and 'json' (uploaded files)
   */
  source = signal<SourceType>('figma');
  
  /*
   * Signal that triggers the test case generation process.
   * Incremented when user clicks "Generate Test Cases" button.
   * The ReviewAndRun component watches this signal via input() and reacts to changes.
   */
  generateTestCasesTrigger = signal(0);

  /*
   * Event handler for source selection (Figma or JSON).
   * Updates the source signal and optionally loads JSON files if switching to JSON source.
   */
  setSource(s: SourceType) {
    this.source.set(s);
    /* When user switches to JSON source, load cached files if not already loaded */
    if (s === 'json' && !this.hasLoadedJsonFiles) {
      this.loadJsonFiles();
    }
  }

  /*
   * ViewChild references to child components for direct method calls and data access.
   * - mainEl: Main content container for scroll positioning
   * - jsonPanel: JSON files display panel (Step 1)
   * - prdUpload: PRD Upload component (Step 2)
   * - reviewAndRun: Review and Run component (Step 3)
   */
  @ViewChild('mainEl') mainEl?: ElementRef<HTMLElement>;
  @ViewChild(PrdUpload) prdUpload?: PrdUpload;
  @ViewChild(ReviewAndRun) reviewAndRun?: ReviewAndRun;
  @ViewChild(DfJsonPanelComponent) jsonPanel?: DfJsonPanelComponent;

  private destroyRef = inject(DestroyRef);
  
  /* Flag to prevent multiple JSON file load requests */
  private hasLoadedJsonFiles = false;

  constructor(
    private api: ApiService,
    private storageService: StorageService,
    private cdr: ChangeDetectorRef
  ) {
    this.getFilesByCacheId();
  }

  /* ==================== Navigation Section ==================== */

  /*
   * Navigate backward to the previous step.
   * Only allowed if not at the first step.
   * Scrolls the main content area to the top for better UX.
   */
  back() {
    if (!this.canGoBack) return;
    this.activeIndex--;
    this.scrollMainToTop();
  }

  /*
   * Navigate to a specific step by index.
   * Validates that the index is within valid range.
   * Scrolls the main content area to the top.
   */
  gotoStep(i: number) {
    if (i < 0 || i >= this.steps.length) return;
    this.activeIndex = i;
    this.scrollMainToTop();
  }

  /*
   * Scrolls the main content container to the top.
   * Improves UX when transitioning between steps.
   */
  private scrollMainToTop() {
    const host = this.mainEl?.nativeElement;
    if (host) host.scrollTo({ top: 0, behavior: 'auto' });
  }

  /* ==================== Button Logic Section ==================== */

  /*
   * Determines the label for the primary action button based on the current step.
   * 
   * Step 1 (Design Source): "Continue"
   * Step 2 (PRD Upload): "Start Analysis" or "Generate Test Cases" (depending on analysis status)
   * Step 3 (Review & Run): "Continue"
   */
  get primaryButtonLabel(): string {
    if (this.activeIndex === 1) {
      return this.prdUpload?.analysisDone
        ? 'Generate Test Cases'
        : 'Start Analysis';
    }
    return 'Continue';
  }

  /*
   * Handles the primary action button click with context-aware logic.
   * 
   * Flow:
   * - If not on Step 2 (PRD Upload): Advance to the next step
   * - If on Step 2 and analysis not done: Start the analysis
   * - If on Step 2 and analysis complete: Trigger test case generation and advance to Step 3
   * 
   * Uses signal to communicate with ReviewAndRun component when generating test cases.
   */
  onPrimaryClick() {
    /* If not on PRD Upload step, simply advance to next step */
    if (this.activeIndex !== 1) {
      this.activeIndex++;
      this.scrollMainToTop();
      return;
    }

    /* If on PRD Upload step but analysis not yet done, start analysis */
    if (!this.prdUpload?.analysisDone) {
      this.prdUpload?.analyze();
      return;
    }

    /*
     * If analysis is complete, trigger test case generation.
     * Process:
     * 1. Advance to Review & Run step
     * 2. Force change detection to instantiate the ReviewAndRun component
     * 3. Increment the generateTestCasesTrigger signal to notify ReviewAndRun
     * 4. Scroll to top for better UX
     */
    this.activeIndex++;
    this.cdr.detectChanges();
    this.generateTestCasesTrigger.update(v => v + 1);
    this.scrollMainToTop();
  }

  /* ==================== Keyboard Handling Section ==================== */

  /*
   * Handles keyboard events on design source cards (Figma/JSON selection).
   * Allows users to select a source by pressing Enter or Spacebar.
   * Improves accessibility for keyboard-only users.
   */
  onCardKey(event: KeyboardEvent, s: SourceType) {
    const key = event.key?.toLowerCase();
    if (key === 'enter' || key === ' ') {
      event.preventDefault();
      this.setSource(s);
    }
  }

  /* ==================== JSON Files Loading Section ==================== */

  /*
   * Loads cached JSON design files from the backend when user switches to JSON source.
   * 
   * Process:
   * 1. Retrieves cache ID from session storage (set when Figma files were fetched earlier)
   * 2. Validates that cache ID exists
   * 3. Marks as loaded to prevent duplicate requests
   * 4. Calls API to fetch files by cache ID
   * 5. On success: Stores files and refreshes JSON panel UI
   * 6. On error: Logs error and resets flag to allow retry
   */
  private loadJsonFiles() {
    /* Retrieve the cached Figma data ID from session storage */
    const cachedIdStr = sessionStorage.getItem('design_files_figma_data');
    
    if (!cachedIdStr) {
      console.warn('No cached figma data found in sessionStorage');
      return;
    }

    try {
      /* Parse the cached data from JSON string */
      const cachedData = JSON.parse(cachedIdStr);
      const cachedId = cachedData?.cacheId;

      if (!cachedId) {
        console.warn('Cache ID is missing from sessionStorage');
        return;
      }

      /*
       * Mark as loaded BEFORE making API call to prevent concurrent requests.
       * This flag acts as a guard against multiple simultaneous loads.
       */
      this.hasLoadedJsonFiles = true;
      
      /*
       * Fetch the design files from the backend API using the cache ID.
       * Subscription is automatically cleaned up when component is destroyed.
       */
      this.api.getFilesByCacheId(cachedId)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: (res) => {
            /* Store the fetched files in the storage service */
            this.storageService.setDesignFilesJsonData(res);
            
            /* Notify the JSON panel to refresh its display with fetched files */
            this.jsonPanel?.refresh();
            console.log('JSON files loaded successfully');
          },
          error: (err) => {
            /* Error handling: Log error and reset flag to allow retry on next attempt */
            console.error('Failed to load JSON files:', err);
            this.hasLoadedJsonFiles = false;
          }
        });
    } catch (e) {
      /* Handle JSON parsing errors gracefully */
      console.error('Error parsing cached data:', e);
    }
  }

  /*
   * Sets up an effect to track source signal changes.
   * Currently minimal usage - just watches the source signal.
   * Actual loading logic is triggered by setSource() method, not by this effect.
   * 
   * Kept separate to avoid multiple signal dependencies and ensure clean architecture.
   */
  private getFilesByCacheId() {
    effect(() => {
      /* Access the source signal to register it as a dependency for this effect */
      this.source();
      /* Actual loading is handled by setSource() method */
    });
  }
}