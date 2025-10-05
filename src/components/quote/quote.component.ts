import { Component, ChangeDetectionStrategy, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PolicyService, PolicyHolder, QuoteDetails } from '../../services/policy.service';

@Component({
  selector: 'app-quote',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './quote.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class QuoteComponent {
  private policyService = inject(PolicyService);

  applicationId = signal('151547');
  policyHolder = signal<PolicyHolder | null>(null);
  insuredAmount = signal<number | null>(null);
  months = signal<number | null>(null);
  cuotas = signal<number | null>(null);
  rentalType = signal<string | null>(null);

  quoteResult = signal<QuoteDetails | null>(null);
  
  isLoadingPolicyHolder = signal(false);
  isLoadingQuote = signal(false);
  policyHolderError = signal<string | null>(null);
  calculationError = signal<string | null>(null);

  constructor() {
    this.fetchPolicyHolder();
  }

  onApplicationIdChange(event: Event) {
    this.applicationId.set((event.target as HTMLInputElement).value);
  }

  onInsuredAmountChange(event: Event) {
    const value = (event.target as HTMLInputElement).value;
    this.insuredAmount.set(value ? parseFloat(value) : null);
  }

  onMonthsChange(event: Event) {
    const value = (event.target as HTMLInputElement).value;
    this.months.set(value ? parseInt(value, 10) : null);
  }

  onCuotasChange(event: Event) {
    const value = (event.target as HTMLSelectElement).value;
    this.cuotas.set(value ? parseInt(value, 10) : null);
  }

  // establecer valor por defecto de cuotas cuando se inicializa el componente
  ngOnInit() {
    if (this.cuotas() === null) {
      this.cuotas.set(1);
    }
  }

  onRentalTypeChange(event: Event) {
    const value = (event.target as HTMLSelectElement).value;
    // guard values expected: 'F' | 'U' | 'C'
    this.rentalType.set(value || null);
  }

  async fetchPolicyHolder() {
    const sa = this.insuredAmount();
    const m = this.months();
    if (!sa || !m || sa <= 0 || m <= 0) {
      this.calculationError.set('Por favor, ingrese una suma asegurada y meses válidos.');
      return;
    }
    if (!this.applicationId()) return;
    this.isLoadingPolicyHolder.set(true);
    this.policyHolderError.set(null);
    this.policyHolder.set(null);
    this.resetQuote();
    try {
      const holder = await this.policyService.getPolicyHolder(this.applicationId(), sa, m);
      this.policyHolder.set(holder);
  // Inicializar el tipo de alquiler al obtener el tomador (usar código corto)
  this.rentalType.set('F');
    } catch (e: any) {
      this.policyHolderError.set(e.message || 'Error al buscar el tomador.');
    } finally {
      this.isLoadingPolicyHolder.set(false);
    }
  }

  async calculateQuote() {

    const appId = this.applicationId();
    const premio = this.insuredAmount();
    const meses = this.months();

    this.quoteResult.set(null);

    
    this.calculationError.set(null);
    this.isLoadingQuote.set(true);

    try {
  const quoteDetails = await this.policyService.calculateQuote(appId, premio, meses, this.rentalType() || undefined, this.cuotas() ?? undefined);
      this.quoteResult.set(quoteDetails);
    } catch (e) {
      this.calculationError.set('Ocurrió un error al calcular la cotización.');
    } finally {
      this.isLoadingQuote.set(false);
    }
  }

  resetQuote() {
    //this.insuredAmount.set(null);
    //this.months.set(null);
    this.quoteResult.set(null);
    this.calculationError.set(null);
  }
}
