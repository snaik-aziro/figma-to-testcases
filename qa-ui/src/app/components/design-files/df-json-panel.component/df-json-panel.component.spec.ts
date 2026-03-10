import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DfJsonPanelComponent } from './df-json-panel.component';

describe('DfJsonPanelComponent', () => {
  let component: DfJsonPanelComponent;
  let fixture: ComponentFixture<DfJsonPanelComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DfJsonPanelComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DfJsonPanelComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
