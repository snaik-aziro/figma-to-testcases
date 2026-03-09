import { Component, Input } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatTooltipModule } from '@angular/material/tooltip';

export interface NavItem {
  label: string;
  icon: string;         // material icon name (outlined style)
  link: string | any[]; // router link
  exact?: boolean;      // true => exact matching
  disabled?: boolean;
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, MatIconModule, MatDividerModule, MatTooltipModule],
  templateUrl: './sidebar.html',
  styleUrls: ['./sidebar.scss']
})
export class Sidebar {
  @Input() collapsed = false;

  navItems: NavItem[] = [
    { label: 'Dashboard',     icon: 'dashboard',    link: ['/dashboard'], exact: true },
    { label: 'Design Files',  icon: 'folder_open',  link: ['/design-files'] },
    { label: 'PRD Library',   icon: 'description',  link: ['/prd-library'] },
    { label: 'Test Cases',    icon: 'fact_check',   link: ['/test-cases'] },
    { label: 'Analysis Runs', icon: 'analytics',    link: ['/analysis-runs'] },
    { label: 'Settings',      icon: 'settings',     link: ['/settings'] }
  ];
}