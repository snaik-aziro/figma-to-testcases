import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DesignFiles } from './design-files';

describe('DesignFiles', () => {
  let component: DesignFiles;
  let fixture: ComponentFixture<DesignFiles>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DesignFiles]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DesignFiles);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
