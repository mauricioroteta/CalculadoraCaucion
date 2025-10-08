import { Injectable } from '@angular/core';

export interface PolicyHolder {
  id: string;
  cuit: string;
  name: string;
  province: string;
  provinceCode: string;
  itemA: number;
  itemB: number;
  itemC: number;
  itemD: number;
  itemE: number;
}

export interface QuoteDetails {
  primaTarifa: number;
  bonificacion: number;
  bonificacionPct: number;
  primaNeta: number;
  recAdministrativo: number;
  recAdministrativoPct: number;
  recFinanciero: number;
  recFinancieroPct: number;
  derEmision: number;
  gastosEscribania: number;
  subtotal: number;
  impuestos: number;
  premio: number;
  tasaAplicada: number;
  sumaAsegurada: number;
  detalleImpuestos?: ImpuestoDetalle[];
}

export interface ImpuestoDetalle {
  impCod: string;
  base: number;
  alicuota: number;
  importe: number;
}

@Injectable({
  providedIn: 'root'
})
export class PolicyService {

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

async getPolicyHolder(applicationId: string, insuredAmount: number, days: number): Promise<PolicyHolder> {
    // We pass days directly instead of months now
    const API_URL = `http://localhost:8000/policyholder/${applicationId}/${insuredAmount}/${days}`;
    console.log(API_URL)
    
    try {
        // Reemplaza 'fetch' con HttpClient si usas @angular/common/http
        const response = await fetch(API_URL, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                // Agrega cabeceras de autenticación si son necesarias
                // 'Authorization': 'Bearer TU_API_KEY'
            }
        });

        if (!response.ok) {
            // Maneja errores de la API (ej. 404 No Encontrado)
            const errorData = await response.json();
            throw new Error(errorData.message || 'Solicitud no encontrada.');
        }

        const holder: PolicyHolder = await response.json();
        return holder;

    } catch (error) {
        console.error('Error fetching policy holder:', error);
        // Lanza un error para que el componente lo pueda mostrar al usuario
        throw new Error('No se pudo obtener la información del tomador.');
    }
}

async calculateQuote(applicationId: string, totalAmount: number, days: number, rentalType?: string, cuotas?: number): Promise<QuoteDetails> {
  await this.delay(800); // Simula latencia de red
  
  // Days are already calculated in component, pass directly
  const dias = days;
  
  // totalAmount already includes insuredAmount + monthlyExpenses
  const premio = totalAmount;
  
  // Calculate estimated months based on days for sumaTotal (for backward compatibility)
  const estimatedMonths = Math.round(days / 30);
  const sumaTotal = premio * estimatedMonths;
  
  // incluir tipo de alquiler (F/U/C) si se provee
  const tipo = rentalType ? `/${rentalType}` : '';
  
  // incluir cuotas si se proveyeron
  const cuotasSeg = cuotas ? `/${cuotas}` : '';
  
  const response = await fetch(`http://localhost:8000/recotizar2/${applicationId}/${premio}/${dias}/${sumaTotal}${cuotasSeg}${tipo}`);
  
  if (!response.ok) {
    throw new Error('No se pudo cargar el archivo de cotizaciones.');
  }

  const quoteParams = await response.json();
  return quoteParams as QuoteDetails;
}
}