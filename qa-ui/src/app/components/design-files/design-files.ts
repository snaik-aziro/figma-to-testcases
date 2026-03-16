import { Component, ContentChild, Input, TemplateRef, ViewChild, ElementRef, signal } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatDividerModule } from '@angular/material/divider';
import { MatTooltipModule } from '@angular/material/tooltip';
import { A11yModule } from '@angular/cdk/a11y';

/* Step‑1 panels (Design Source) */
import { DfFigmaPanelComponent } from './df-figma-panel/df-figma-panel';
import { DfJsonPanelComponent } from './df-json-panel.component/df-json-panel.component';

/* Step‑2 and Step‑3 components (rendered inside MAIN) */
import { PrdUpload } from '../prd-upload/prd-upload';
import { ReviewAndRun } from '../review-and-run/review-and-run';

export interface Steps {
  key: string;
  label: string;
}
type SourceType = 'json' | 'figma';

@Component({
  selector: 'app-design-files',
  standalone: true,
  imports: [
    MatCardModule, MatIconModule, MatButtonModule, MatDividerModule, MatTooltipModule,
    A11yModule,
    /* children that will render inside MAIN */
    DfFigmaPanelComponent, DfJsonPanelComponent,
    PrdUpload, ReviewAndRun
  ],
  templateUrl: './design-files.html',
  styleUrls: ['./design-files.scss']
})
export class DesignFiles {
  /** Steps for the left rail & footer dots (order matters) */
  @Input() steps: Steps[] = [
    { key: 'design', label: 'Design Source' },
    { key: 'prd',    label: 'PRD Upload' },
    { key: 'review', label: 'Review & Run' },
  ];

  /** In‑page step index (0 = Design, 1 = PRD, 2 = Review) */
  activeIndex = 0;

  /** Derived button states */
  get canGoBack(): boolean { return this.activeIndex > 0; }
  get canGoNext(): boolean { return this.activeIndex < this.steps.length - 1; }

  /** Optional projected content */
  @ContentChild('content', { read: TemplateRef }) contentTpl?: TemplateRef<unknown>;

  /** Step‑1: source toggle (UI‑only) */
  source = signal<SourceType>('json');
  setSource(s: SourceType) { this.source.set(s); }

  /** Main scroll container ref (to scroll to top on step change) */
  @ViewChild('mainEl', { static: false }) mainEl?: ElementRef<HTMLElement>;

  back() {
    if (!this.canGoBack) return;
    this.activeIndex--;
    this.scrollMainToTop();
  }

  next() {
    if (!this.canGoNext) return;
    this.activeIndex++;
    this.scrollMainToTop();
  }

  gotoStep(i: number) {
    if (i < 0 || i >= this.steps.length) return;
    this.activeIndex = i;
    this.scrollMainToTop();
  }

  onCardKey(event: KeyboardEvent, s: SourceType) {
    const key = event.key?.toLowerCase();
    if (key === 'enter' || key === ' ') {
      event.preventDefault();
      this.setSource(s);
    }
  }

  private scrollMainToTop() {
    // Smoothly scroll just the MAIN pane, not the page
    const host = this.mainEl?.nativeElement;
    if (host) host.scrollTo({ top: 0, behavior: 'auto' });
  }
}