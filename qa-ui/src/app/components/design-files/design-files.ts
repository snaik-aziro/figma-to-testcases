import { Component, ContentChild, Input, TemplateRef, signal } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatDividerModule } from '@angular/material/divider';
import { MatTooltipModule } from '@angular/material/tooltip';
import { A11yModule } from "@angular/cdk/a11y";

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
    A11yModule
  ],
  templateUrl: './design-files.html',
  styleUrls: ['./design-files.scss']
})
export class DesignFiles {
  /** Left rail + footer dots */
  @Input() steps: Steps[] = [
    { key: 'design', label: 'Design Source' },
    { key: 'prd', label: 'PRD Upload' },
    { key: 'review', label: 'Review & Run' },
  ];

  /** Current step (UI only) */
  @Input() activeIndex = 0;

  /** Footer buttons (UI only) */
  @Input() canGoBack = true;
  @Input() canGoNext = true;

  /** Optional projected content (kept for future) */
  @ContentChild('content', { read: TemplateRef }) contentTpl?: TemplateRef<unknown>;

  /** Toggle state for Design Source */
  source = signal<SourceType>('json'); // default to JSON to match your last screenshot
  setSource(s: SourceType) { this.source.set(s); }
}