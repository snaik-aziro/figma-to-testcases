import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { TestGeneratorService } from '../services/test-generator.service';

@Component({
  selector: 'app-generate-test',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatFormFieldModule, MatInputModule, MatButtonModule],
  template: `
    <h2>Generate Test</h2>
    <form [formGroup]="form" (ngSubmit)="submit()">
      <mat-form-field style="width:400px">
        <input matInput placeholder="Screen ID" formControlName="screenId" />
      </mat-form-field>
      <div>
        <button mat-flat-button color="primary" type="submit" [disabled]="form.invalid">Generate</button>
      </div>
    </form>
    <div *ngIf="result">
      <h3>Result</h3>
      <pre>{{ result | json }}</pre>
    </div>
  `
})
export class GenerateTestComponent {
  form = this.fb.group({ screenId: ['', Validators.required] });
  result: any;
  constructor(private fb: FormBuilder, private gen: TestGeneratorService) {}
  submit() {
    if (this.form.valid) {
      this.gen.generate(this.form.value.screenId).subscribe(res => (this.result = res));
    }
  }
}
