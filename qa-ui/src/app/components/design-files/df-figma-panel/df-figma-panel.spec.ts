import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DfFigmaPanel } from './df-figma-panel';

describe('DfFigmaPanel', () => {
  let component: DfFigmaPanel;
  let fixture: ComponentFixture<DfFigmaPanel>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DfFigmaPanel]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DfFigmaPanel);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
