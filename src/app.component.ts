import { Component, ChangeDetectionStrategy } from '@angular/core';
import { QuoteComponent } from './components/quote/quote.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [QuoteComponent],
  templateUrl: './app.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppComponent {}