# Cotizador de Póliza de Caución - Angular App

Esta aplicación de Angular es una herramienta para cotizar pólizas de seguro de caución. Actualmente, utiliza archivos JSON locales para simular las respuestas de un backend, lo que facilita el desarrollo y las pruebas del frontend de forma aislada.

## Estructura del Proyecto

-   `/src/components/quote/`: Contiene el componente principal de la aplicación para la cotización.
-   `/src/services/policy.service.ts`: Contiene la lógica de negocio. **Este es el único archivo que necesitarás modificar para conectar a un backend real.**
-   `/src/assets/data/`: Contiene los archivos JSON que simulan la base de datos.
    -   `policy-holders.json`: Lista de tomadores de póliza de prueba.
    -   `quotes.json`: Parámetros de cotización para cada tomador.

## Cómo conectar a un Backend Real

Para que la aplicación consuma datos de tus servicios reales (por ejemplo, una API hecha en Python), sigue estos pasos. Solo necesitas editar el archivo `src/services/policy.service.ts`.

### Paso 1: Modificar `getPolicyHolder`

Este método busca los datos de un tomador de póliza por su número de solicitud.

**Código actual (simulado con JSON):**
```typescript
async getPolicyHolder(applicationId: string): Promise<PolicyHolder> {
    await this.delay(500); // Simula latencia de red
    const response = await fetch('src/assets/data/policy-holders.json');
    // ... lógica para buscar en el JSON
}
```

**Código modificado para llamar a una API real:**

Reemplaza el contenido del método con una llamada a tu endpoint. Asume que tu API tiene un endpoint `GET /api/policy-holder/{applicationId}`.

```typescript
async getPolicyHolder(applicationId: string): Promise<PolicyHolder> {
    const API_URL = `https://tu-backend.com/api/policy-holder/${applicationId}`;
    
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
```

### Paso 2: Modificar `calculateQuote`

Este método envía los datos del formulario al backend para obtener los cálculos de la cotización.

**Código actual (simulado con JSON):**
```typescript
async calculateQuote(applicationId: string, insuredAmount: number, months: number): Promise<QuoteDetails> {
    await this.delay(800);
    const response = await fetch('src/assets/data/quotes.json');
    // ... lógica de cálculo basada en el JSON
}
```

**Código modificado para llamar a una API real:**

Reemplaza el contenido del método para que haga una petición `POST` a tu endpoint de cálculo. Asume que tu API tiene un endpoint `POST /api/quote/calculate`.

```typescript
async calculateQuote(applicationId: string, insuredAmount: number, months: number): Promise<QuoteDetails> {
    const API_URL = 'https://tu-backend.com/api/quote/calculate';

    const requestBody = {
        applicationId,
        insuredAmount,
        months
    };

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // 'Authorization': 'Bearer TU_API_KEY'
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Error en el cálculo del servidor.');
        }

        const quoteDetails: QuoteDetails = await response.json();
        return quoteDetails;

    } catch (error) {
        console.error('Error calculating quote:', error);
        throw new Error('Ocurrió un error al calcular la cotización.');
    }
}
```

### Consideraciones Adicionales

-   **Manejo de CORS:** Asegúrate de que tu backend esté configurado para aceptar peticiones desde el dominio donde se ejecuta tu aplicación Angular.
-   **Variables de Entorno:** Para mayor seguridad y flexibilidad, considera almacenar la URL base de tu API en variables de entorno.
-   **HttpClient de Angular:** Para aplicaciones más complejas, se recomienda usar el `HttpClientModule` de Angular, ya que ofrece funcionalidades avanzadas como interceptores, manejo de errores robusto y tipado fuerte.