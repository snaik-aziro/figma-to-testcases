import { Component, signal, ChangeDetectionStrategy } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Header } from './shared/header/header';
import { Sidebar } from './shared/sidebar/sidebar';
import { LoaderService } from './services/loader-service/loader-service';
import { Observable } from 'rxjs/internal/Observable';
import { Loader } from './shared/loader/loader';
import { AsyncPipe } from '@angular/common';
@Component({
  selector: 'app-root',
  imports: [RouterOutlet, Header, Sidebar, Loader, AsyncPipe],
  standalone: true,
  templateUrl: './app.html',
  styleUrl: './app.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class App {
  loading$!: Observable<boolean>;

  constructor(private loader: LoaderService) {
  this.loading$ = this.loader.loading$;
  }

  protected readonly title = signal('qa-ui');
}
