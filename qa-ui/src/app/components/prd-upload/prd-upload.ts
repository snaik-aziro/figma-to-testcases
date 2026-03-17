import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-prd-upload',
  imports: [MatCardModule, MatIconModule, MatButtonModule],
  templateUrl: './prd-upload.html',
  styleUrl: './prd-upload.scss',
})
export class PrdUpload {

}
