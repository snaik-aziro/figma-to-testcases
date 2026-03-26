import { Component } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatButtonModule } from '@angular/material/button';
import { Loader } from '../../shared/loader/loader';

@Component({
  selector: 'app-review-and-run',
  standalone: true,
  imports: [
    MatIconModule,
    MatCardModule,
    MatExpansionModule,
    MatButtonModule,
    Loader
  ],
  templateUrl: './review-and-run.html',
  styleUrls: ['./review-and-run.scss']
})
export class ReviewAndRun {}