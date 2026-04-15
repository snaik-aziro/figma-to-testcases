import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDividerModule } from '@angular/material/divider';
import { MatBadgeModule } from '@angular/material/badge';
import { MatMenuModule } from '@angular/material/menu';
@Component({
  selector: 'app-header',
  standalone: true,
  imports: [
    MatToolbarModule,
    MatIconModule,
    MatTooltipModule,
    MatDividerModule,
    MatBadgeModule,
    MatMenuModule
  ],
  templateUrl: './header.html',
  styleUrls: ['./header.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class Header {

/** Notifications count (plain number, NOT a signal) */
  @Input() unreadCount: number | null = 0;

  /** Profile inputs */
  @Input() userName = 'Ganesh More';
  @Input() avatarUrl: string | null = null;  // e.g. 'assets/avatars/ganesh.jpg'

  /** Fallback initials if no avatar */
  get userInitials(): string {
    const parts = (this.userName || '').trim().split(/\s+/);
    const a = parts[0]?.[0] ?? '';
    const b = parts[1]?.[0] ?? '';
    return (a + b).toUpperCase();
  }

  onHelp() {
    // TODO: open help
  }

  onNotification() {
    // TODO: open notifications
  }

}
