import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PrdUpload } from './prd-upload';

describe('PrdUpload', () => {
  let component: PrdUpload;
  let fixture: ComponentFixture<PrdUpload>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PrdUpload]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PrdUpload);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
