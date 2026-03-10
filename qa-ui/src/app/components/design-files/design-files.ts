import { Component, ContentChild, Input, TemplateRef, signal } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatDividerModule } from '@angular/material/divider';
import { MatTooltipModule } from '@angular/material/tooltip';
import { A11yModule } from '@angular/cdk/a11y';

/* Child panels */
import { DfFigmaPanelComponent } from './df-figma-panel/df-figma-panel';
import { DfJsonPanelComponent } from './df-json-panel.component/df-json-panel.component';

export interface Steps {
  key: string;
  label: string;
}
type SourceType = 'json' | 'figma';

@Component({
  selector: 'app-design-files',
  standalone: true,
  imports: [
    /* Angular Material */
    MatCardModule, MatIconModule, MatButtonModule, MatDividerModule, MatTooltipModule,
    /* A11y */
    A11yModule,
    /* Child components */
    DfFigmaPanelComponent, DfJsonPanelComponent
  ],
  templateUrl: './design-files.html',
  styleUrls: ['./design-files.scss']
})
export class DesignFiles {
  /** Left rail + footer dots */
  @Input() steps: Steps[] = [
    { key: 'design', label: 'Design Source' },
    { key: 'prd',    label: 'PRD Upload' },
    { key: 'review', label: 'Review & Run' },
  ];

  /** Current step (UI only) */
  @Input() activeIndex = 0;

  /** Footer buttons (UI only) */
  @Input() canGoBack = true;
  @Input() canGoNext = true;

  /** Optional projected content (kept for future) */
  @ContentChild('content', { read: TemplateRef }) contentTpl?: TemplateRef<unknown>;

  /** Toggle state for Design Source (UI-only) */
  source = signal<SourceType>('json');
  setSource(s: SourceType) { this.source.set(s); }

  /** Keyboard support on cards */
  onCardKey(event: KeyboardEvent, s: SourceType) {
    const key = event.key?.toLowerCase();
    if (key === 'enter' || key === ' ') {
      event.preventDefault();
      this.setSource(s);
    }
  }
}