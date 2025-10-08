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
  monthlyExpenses = signal<number | null>(null);
  fromDate = signal<string>(this.getFormattedDate());
  toDate = signal<string>(this.getFormattedDate(12)); // Default to 12 months later
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

  // Helper method to format dates for date inputs
  private getFormattedDate(monthsToAdd: number = 0): string {
    const date = new Date();
    if (monthsToAdd) {
      date.setMonth(date.getMonth() + monthsToAdd);
    }
    return date.toISOString().split('T')[0]; // Returns YYYY-MM-DD format
  }

  onApplicationIdChange(event: Event) {
    this.applicationId.set((event.target as HTMLInputElement).value);
  }

  onInsuredAmountChange(event: Event) {
    const value = (event.target as HTMLInputElement).value;
    this.insuredAmount.set(value ? parseFloat(value) : null);
  }
  
  onMonthlyExpensesChange(event: Event) {
    const value = (event.target as HTMLInputElement).value;
    this.monthlyExpenses.set(value ? parseFloat(value) : null);
  }

  onFromDateChange(event: Event) {
    const value = (event.target as HTMLInputElement).value;
    this.fromDate.set(value);
  }

  onToDateChange(event: Event) {
    const value = (event.target as HTMLInputElement).value;
    this.toDate.set(value);
  }

  onCuotasChange(event: Event) {
    const value = (event.target as HTMLSelectElement).value;
    this.cuotas.set(value ? parseInt(value, 10) : null);
  }
  
  // Calculate days between two dates
  private calculateDaysBetween(fromDate: string, toDate: string): number {
    const start = new Date(fromDate);
    const end = new Date(toDate);
    const diffTime = Math.abs(end.getTime() - start.getTime());
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
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
    const insuredAmount = this.insuredAmount();
    const expenses = this.monthlyExpenses() || 0;
    const totalAmount = insuredAmount ? insuredAmount + expenses : null;
    
    const days = this.calculateDaysBetween(this.fromDate(), this.toDate());
    
    if (!totalAmount || totalAmount <= 0 || days <= 0) {
      this.calculationError.set('Por favor, ingrese valores válidos para suma asegurada, expensas y fechas.');
      return;
    }
    
    if (!this.applicationId()) return;
    this.isLoadingPolicyHolder.set(true);
    this.policyHolderError.set(null);
    this.policyHolder.set(null);
    this.resetQuote();
    
    try {
      // Pass calculated days instead of months
      const holder = await this.policyService.getPolicyHolder(this.applicationId(), totalAmount, days);
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
    const insuredAmount = this.insuredAmount();
    const expenses = this.monthlyExpenses() || 0;
    const totalAmount = insuredAmount ? insuredAmount + expenses : null;
    
    const days = this.calculateDaysBetween(this.fromDate(), this.toDate());

    if (!totalAmount || !days) {
      this.calculationError.set('Datos incompletos para calcular.');
      return;
    }

    this.quoteResult.set(null);
    this.calculationError.set(null);
    this.isLoadingQuote.set(true);

    try {
      const quoteDetails = await this.policyService.calculateQuote(
        appId, 
        totalAmount, 
        days, 
        this.rentalType() || undefined, 
        this.cuotas() ?? undefined
      );
      this.quoteResult.set(quoteDetails);
    } catch (e) {
      this.calculationError.set('Ocurrió un error al calcular la cotización.');
    } finally {
      this.isLoadingQuote.set(false);
    }
  }

  resetQuote() {
    //this.insuredAmount.set(null);
    //this.monthlyExpenses.set(null);
    //this.fromDate.set(this.getFormattedDate());
    //this.toDate.set(this.getFormattedDate(12));
    this.quoteResult.set(null);
    this.calculationError.set(null);
  }
}
