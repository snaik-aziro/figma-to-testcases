import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ReviewAndRun } from './review-and-run';

describe('ReviewAndRun', () => {
  let component: ReviewAndRun;
  let fixture: ComponentFixture<ReviewAndRun>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReviewAndRun]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ReviewAndRun);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
