import { Component } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { StorageService } from '../../../shared/services/storage-service';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';

@Component({
  selector: 'app-df-json-panel',
  standalone: true,
  imports: [MatCardModule, MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule,
    MatSelectModule,
  ],
  templateUrl: './df-json-panel.component.html',
  styleUrls: ['./df-json-panel.component.scss']
})
export class DfJsonPanelComponent {

  cachedFiles: any[] = [];

  constructor(private storageService: StorageService) { }

  ngOnInit(): void {
    const stored = this.storageService.getDesignFilesJsonData();
    this.cachedFiles = stored ? (Array.isArray(stored) ? stored : [stored]) : [];
  }

  onCachedIndexSelect(event: Event): void {
    const selectedIndex = +(event.target as HTMLSelectElement).value;

    if (isNaN(selectedIndex)) return;

    const selectedFile = this.cachedFiles[selectedIndex];

    this.storageService.setDesignFilesJsonData(selectedFile);
    console.log('Selected cached design:', selectedFile);
  }
}
