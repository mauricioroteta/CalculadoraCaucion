from turtle import pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pyodbc
import pandas as pd
from typing import List
# Configuración de la conexión a SQL Server
from dotenv import load_dotenv
import os
class ImpuestoDetalle(BaseModel):
    impCod: str
    base: float
    alicuota: float
    importe: float

# Cargar la tabla de derechos de emisión
deremi_df = pd.read_excel("deremi.xlsx")

# Asegurarse que los nombres de columnas estén limpios
deremi_df.columns = deremi_df.columns.str.strip()


app = FastAPI()


class impDetail(BaseModel):
    impCod: str
    sol2Base: float
    sol2Ali: float
    sol2Imp: float

# ...después de crear app...
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # O especifica ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# carga .env si existe
load_dotenv()  

DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

if not all([DB_SERVER, DB_DATABASE, DB_USERNAME, DB_PASSWORD]):
    raise RuntimeError("Faltan variables de configuración. Ver .env o variables de entorno.")

conn_str = (
    f'DRIVER={{SQL Server}};'
    f'SERVER={DB_SERVER};'
    f'DATABASE={DB_DATABASE};'
    f'UID={DB_USERNAME};'
    f'PWD={DB_PASSWORD}'
)

class PolicyHolder(BaseModel):
    id: str
    cuit: str
    name: str
    province: str
    provinceCode: str
    itemA: float
    itemB: float
    itemC: float
    itemD: float
    itemE: float

class QuoteDetails(BaseModel):
    primaTarifa: float
    bonificacion: float
    bonificacionPct: float
    primaNeta: float
    recAdministrativo: float
    recAdministrativoPct: float
    recFinanciero: float
    recFinancieroPct: float
    derEmision: float
    gastosEscribania: float
    subtotal: float
    impuestos: float
    # nueva sublista de impuestos
    detalleImpuestos: List[ImpuestoDetalle] = []
    premio: float
    tasaAplicada: float
    sumaAsegurada: float

# Datos de ejemplo
policyholders = {
    "151547": PolicyHolder(
        id="151547",
        cuit="20-12345678-9",
        name="Juan Perez",
        province="Buenos Aires",
        provinceCode="BA",
        itemA=100,
        itemB=0,
        itemC=125,
        itemD=100,
        itemE=175
    )
}

quotes = {
    "151547": QuoteDetails(
        primaTarifa=1000,
        bonificacion=100,
        bonificacionPct=10,
        primaNeta=900,
        recAdministrativo=50,
        recAdministrativoPct=5,
        recFinanciero=20,
        recFinancieroPct=2,
        derEmision=30,
        gastosEscribania=10,
        subtotal=1010,
        impuestos=200,
        premio=5000,
        tasaAplicada=0.5,
        sumaAsegurada=100000
    )
}

@app.get("/impDetail/{application_id}/", response_model=list[impDetail])
def get_taxes(application_id: str):
    query = """
    select ImpCod, Sol2Base, Sol2Ali, Sol2Imp
    from SolImp s
    where s.EmpCod = 1 and s.RamCod = 9 and s.SolNro = ?
    """
    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute(query, application_id)
            rows = cursor.fetchall()
            if rows:
                return [
                    impDetail(
                        impCod=row.ImpCod,
                        sol2Base=row.Sol2Base,
                        sol2Ali=row.Sol2Ali,
                        sol2Imp=row.Sol2Imp 
                    )
                    for row in rows
                ]
            else:
                raise HTTPException(status_code=404, detail="No taxes found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/policyholder/{application_id}/{sumaAseg}/{meses}", response_model=PolicyHolder)
def get_policyholder(application_id: str, sumaAseg: int, meses: int):
    query = """
    select p.PerCod as id, p.PerCui as cuit, a.AseNom as name, pro.PrvCod as provinceCode, pro.PrvNom as province,
    (? * ?) * .20 itemA,
    0 itemB,
    (? * ?) * .25 itemC,
    (? * ?) * .20 itemD,
    (? * ?) * .35 itemE,
    c.Sol14TasApl tasaAplicada,
    c.Sol14CapAse sumaAsegurada
    from solici s
    left join TomCau tc on tc.TCauCod = s.Sol1TomCod
    left join Aseg a on a.AseCod = tc.TCauAseCod
    left join Personas p on p.PerCod = a.AsePerCod
    left join Personas2 p1 on p1.PerCod = p.PerCod
    left join CodPos cp on cp.CPCod = p1.CPCod and cp.CPSub = p1.CPSub
    left join Provin pro on pro.PrvCod = cp.PrvCod
    left join SolRieCob c on s.EmpCod = c.EmpCod and c.RamCod = s.RamCod and s.SolNro = c.SolNro
    where s.EmpCod = 1 and s.RamCod = 9 and s.SolNro = ?
    """
    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute(query, sumaAseg, meses, sumaAseg, meses, sumaAseg, meses, sumaAseg, meses, application_id)
            row = cursor.fetchone()
            if row:
                return PolicyHolder(
                    id=str(row.id),
                    cuit=row.cuit,
                    name=row.name,
                    provinceCode=row.provinceCode,
                    province=row.province,
                    itemA=row.itemA,
                    itemB=row.itemB,
                    itemC=row.itemC,
                    itemD=row.itemD,
                    itemE=row.itemE
                )
            else:
                raise HTTPException(status_code=404, detail="PolicyHolder not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quote/{application_id}/", response_model=QuoteDetails)
def get_quote(application_id: str):
    query = """
    select 
        s.Sol1Pri as primaTarifa, 
        s.Sol1BonPriPor as bonificacionPct, 
        s.Sol1BonPri as bonificacion,
        s.Sol1Pri + s.Sol1BonPri as primaNeta,
        s.Sol1RAdPor as recAdministrativoPct,
        s.Sol1RAd as recAdministrativo,
        s.Sol1RFiPor as recFinancieroPct,
        s.Sol1RFin as recFinanciero,
        s.Sol1DEm as derEmision,
        s.Sol1OtrCar as gastosEscribania,
        s.Sol1Pri + s.Sol1BonPri + s.Sol1RAdPor + s.Sol1RAd + s.Sol1RFiPor + s.Sol1RFin + s.Sol1DEm as subtotal,
        s.Sol1Imp as impuestos,
        s.Sol1Pre as premio,
        c.Sol14TasApl tasaAplicada,
        c.Sol14CapAse sumaAsegurada     
    from solici s 
    left join SolRieCob c on s.EmpCod = c.EmpCod and c.RamCod = s.RamCod and s.SolNro = c.SolNro
    where s.EmpCod = 1 and s.RamCod = 9 and s.SolNro = ?
    """
    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute(query, application_id)
            row = cursor.fetchone()
            if row:
                return QuoteDetails(
                    primaTarifa=row.primaTarifa,
                    bonificacion=row.bonificacion,
                    bonificacionPct=row.bonificacionPct,
                    primaNeta=row.primaNeta,
                    recAdministrativo=row.recAdministrativo,
                    recAdministrativoPct=row.recAdministrativoPct,
                    recFinanciero=row.recFinanciero,
                    recFinancieroPct=row.recFinancieroPct,
                    derEmision=row.derEmision,
                    gastosEscribania=row.gastosEscribania,
                    subtotal=row.subtotal,
                    impuestos=row.impuestos,
                    premio=row.premio,
                    tasaAplicada=row.tasaAplicada,
                    sumaAsegurada=row.sumaAsegurada 
                )
            else:
                raise HTTPException(status_code=404, detail="Quote not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@app.get("/recotizar/{application_id}/{premioinformado}/{dias}/", response_model=QuoteDetails)
def get_quote(application_id: str, premioinformado: float, dias: int):
    query = """
    select 
        s.Sol1Pri as primaTarifa, 
        s.Sol1BonPriPor as bonificacionPct, 
        s.Sol1BonPri as bonificacion,
        s.Sol1Pri + s.Sol1BonPri as primaNeta,
        s.Sol1RAdPor as recAdministrativoPct,
        s.Sol1RAd as recAdministrativo,
        s.Sol1RFiPor as recFinancieroPct,
        s.Sol1RFin as recFinanciero,
        s.Sol1DEm as derEmision,
        s.Sol1OtrCar as gastosEscribania,
        s.Sol1Pri + s.Sol1BonPri + s.Sol1RAdPor + s.Sol1RAd + s.Sol1RFiPor + s.Sol1RFin + s.Sol1DEm as subtotal,
        s.Sol1Imp as impuestos,
        s.Sol1Pre as premio,
        c.Sol14TasApl tasaAplicada,
                                        bonificacion=0.0,
                                        bonificacionPct=0.0,
    left join SolRieCob c on s.EmpCod = c.EmpCod and c.RamCod = s.RamCod and s.SolNro = c.SolNro
    where s.EmpCod = 1 and s.RamCod = 9 and s.SolNro = ?
    """

    query_impuestos = """
    select ImpCod, Sol2Base, Sol2Ali, Sol2Imp
    from SolImp s
    where s.EmpCod = 1 and s.RamCod = 9 and s.SolNro = ?
    """

    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            
            # consulta principal
            cursor.execute(query, application_id)
            row = cursor.fetchone()

            if row:
                # cálculo de nueva prima
                nueva_prima_tarifa = (row.tasaAplicada * row.sumaAsegurada) / 1000 / 365 * dias
                nuevo_recargo_adm = nueva_prima_tarifa * (row.recAdministrativoPct / 100)
                nuevo_der_emision = obtener_derecho(nueva_prima_tarifa)
                nuevo_sub_total = (float(nueva_prima_tarifa)) + (float(nuevo_der_emision)) + (float(nuevo_recargo_adm))
                subtotal_orig = float(row.primaTarifa) + float(row.derEmision) + float(row.recFinanciero) + float(row.recAdministrativo)
                print(subtotal_orig)

                # Consulta de detalle de impuestos
                cursor.execute(query_impuestos, application_id)
                impuestos_rows = cursor.fetchall()
                detalle_impuestos = [
                    ImpuestoDetalle(
                        impCod=str(r.ImpCod),
                        base=float(r.Sol2Base),
                        alicuota=float(r.Sol2Ali),
                        importe=float(r.Sol2Imp),
                    )
                    for r in impuestos_rows
                ]
                
                # Recalcular importe impuesto parta base = subtotal_orig
                for imp in detalle_impuestos:
                    if imp.base == subtotal_orig:
                        imp.base = round(float(nuevo_sub_total), 2)
                        imp.importe = round((float(imp.alicuota) / 100) * float(imp.base), 2)
                    else:
                        imp.base = 0.0
                        imp.importe = 0.0
                
                # Recalcular impuestos totales
                nuevo_impuestos = 0.0
                for imp in detalle_impuestos:
                    nuevo_impuestos = round(imp.importe, 2) + nuevo_impuestos

                # Recalcular importe impuesto = 0 ( casos especiales )
                for imp in detalle_impuestos:
                    if imp.base == 0:
                        imp.base = round(float(nuevo_impuestos) + float(nuevo_sub_total), 2)
                        imp.importe = round((float(imp.alicuota) / 100) * float(imp.base), 2)

                # Recalcular impuestos totales
                nuevo_impuestos = 0.0
                for imp in detalle_impuestos:
                    nuevo_impuestos = round(imp.importe, 2) + nuevo_impuestos

                nuevo_premio = (float(nueva_prima_tarifa)) + (float(nuevo_der_emision)) + (float(nuevo_recargo_adm) + float(nuevo_impuestos))

                # respuesta final
                return QuoteDetails(
                    primaTarifa=round(nueva_prima_tarifa, 2),
                    bonificacion=row.bonificacion,
                    bonificacionPct=row.bonificacionPct,
                    primaNeta=round(nueva_prima_tarifa, 2),
                    recAdministrativo=round(nuevo_recargo_adm, 2),
                    recAdministrativoPct=row.recAdministrativoPct,
                    recFinanciero=row.recFinanciero,
                    recFinancieroPct=row.recFinancieroPct,
                    derEmision=nuevo_der_emision,
                    gastosEscribania=row.gastosEscribania,
                    subtotal=round(nuevo_sub_total, 2),
                    impuestos=nuevo_impuestos,
                    premio=round(nuevo_premio, 2),
                    tasaAplicada=row.tasaAplicada,
                    sumaAsegurada=row.sumaAsegurada,
                    detalleImpuestos=detalle_impuestos
                )
            else:
                raise HTTPException(status_code=404, detail="Quote not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

def obtener_derecho(prima: float) -> float:
    # Filtrar las filas con PRIMA <= prima
    candidatos = deremi_df[deremi_df["PRIMA"] <= prima]

    if candidatos.empty:
        # Si no hay ninguna prima menor o igual, devolvemos el mínimo
        return float(deremi_df["DERECHO"].iloc[0])
    else:
        # Elegir la PRIMA más cercana (la máxima que cumpla la condición)
        fila = candidatos.loc[candidatos["PRIMA"].idxmax()]
        return float(fila["DERECHO"])


@app.get("/recotizar2/{application_id}/{premioinformado}/{dias}/", response_model=QuoteDetails)
def get_quote(application_id: str, premioinformado: int, dias: int):
    # Ruta histórica sin sumaTotal ni tipo. Por compatibilidad llamamos al handler común con sumaTotal=None y tipo 'F' por defecto.
    return _get_quote_internal(application_id, premioinformado, dias, None, 'F')


@app.get("/recotizar2/{application_id}/{premioinformado}/{dias}/{tipo}", response_model=QuoteDetails)
def get_quote_with_type(application_id: str, premioinformado: int, dias: int, tipo: str):
    # tipo esperado: 'F', 'U', 'C' - sin sumaTotal
    tipo = tipo.upper() if tipo else 'F'
    return _get_quote_internal(application_id, premioinformado, dias, None, tipo)


@app.get("/recotizar2/{application_id}/{premioinformado}/{dias}/{sumaTotal}/{tipo}", response_model=QuoteDetails)
def get_quote_with_suma(application_id: str, premioinformado: int, dias: int, sumaTotal: float, tipo: str):
    tipo = tipo.upper() if tipo else 'F'
    return _get_quote_internal(application_id, premioinformado, dias, float(sumaTotal), tipo)


@app.get("/recotizar2/{application_id}/{premioinformado}/{dias}/{sumaTotal}/{cuotas}/{tipo}", response_model=QuoteDetails)
def get_quote_with_suma_and_cuotas(application_id: str, premioinformado: int, dias: int, sumaTotal: float, cuotas: int, tipo: str):
    tipo = tipo.upper() if tipo else 'F'
    # simplemente pasar cuotas al handler; actualmente no se usa en la lógica
    return _get_quote_internal(application_id, premioinformado, dias, float(sumaTotal), tipo, cuotas)


def _get_quote_internal(application_id: str, premioinformado: int, dias: int, sumaTotal: float | None, tipo: str, cuotas: int | None = None):
    query = """
    select 
        s.Sol1Pri as primaTarifa, 
        s.Sol1BonPriPor as bonificacionPct, 
        s.Sol1BonPri as bonificacion,
        s.Sol1Pri + s.Sol1BonPri as primaNeta,
        s.Sol1RAdPor as recAdministrativoPct,
        s.Sol1RAd as recAdministrativo,
        ROUND(s.Sol1RFiPor, 2) as recFinancieroPct,
        s.Sol1RFin as recFinanciero,
        s.Sol1DEm as derEmision,
        s.Sol1OtrCar as gastosEscribania,
        s.Sol1Pri + s.Sol1BonPri + s.Sol1RAd + s.Sol1RFin + s.Sol1DEm as subtotal,
        s.Sol1Imp as impuestos,
        s.Sol1Pre as premio,
        c.Sol14TasApl tasaAplicada,
        c.Sol14CapAse sumaAsegurada,
        datediff(day, s.Sol1VigDesFac, s.Sol1VigHasFac) diasVigencia
    from solici s 
    left join SolRieCob c on s.EmpCod = c.EmpCod and c.RamCod = s.RamCod and s.SolNro = c.SolNro
    where s.EmpCod = 1 and s.RamCod = 9 and s.SolNro = ?
    """

    query_impuestos = """
    select ImpCod, Sol2Base, Sol2Ali, Sol2Imp
    from SolImp s
    where s.EmpCod = 1 and s.RamCod = 9 and s.SolNro = ?
    """

    # Determinar el premio objetivo: si se envió sumaTotal y tipo, calcular según regla
    target_premio = float(premioinformado)
    if sumaTotal is not None:
        t = (tipo or 'F').upper()
        if t == 'F':
            target_premio = (float(sumaTotal) / 100.0) * 4.3
        elif t == 'C':
            target_premio = (float(sumaTotal) / 100.0) * 4.8
        elif t == 'U':
            target_premio = (float(sumaTotal) / 100.0) * 3.0

    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()

            # consulta principal
            cursor.execute(query, application_id)
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Quote not found")

            # consulta impuestos
            cursor.execute(query_impuestos, application_id)
            impuestos_rows = cursor.fetchall()

            # Datos base
            tasa = float(row.tasaAplicada)
            sumaAseg = float(row.sumaAsegurada)
            # sumaTotal enviada por el frontend (premio * meses) — si se envió, la usamos para logging
            if sumaTotal is not None:
                print(f"Suma total recibida desde servicio: {sumaTotal}")
                # Usar la suma total enviada como suma asegurada para los cálculos y la respuesta
                try:
                    sumaAseg = float(sumaTotal)
                except Exception:
                    # si la conversión falla, mantenemos el valor de la DB
                    pass
            # valor de base desde la DB (por referencia); puede ser recalculado según cuotas
            rec_financiero_db = float(row.recFinanciero)
            prima_tarifa_orig = float(row.primaTarifa)
            der_emision_orig = float(row.derEmision)
            rec_adm_monto = float(row.recAdministrativo)
            # Forzar bonificación a 0 según requerimiento
            bonificacion = 0.0
            gastos_escribania = float(row.gastosEscribania)

            # Fijar recargo administrativo en 15% según requerimiento
            rec_admin_pct = 15.0

            # Recargo financiero pct y monto base desde DB (no se modifica por cuotas)
            rec_financiero_pct = float(row.recFinancieroPct)
            rec_financiero_db = float(row.recFinanciero)

            # Determinar incremento sobre el premio según cantidad de cuotas (aumento_pct aplicado al premio final)
            # Valores solicitados (aplican al premio):
            # 1 cuota  -> 0%
            # 3 cuotas -> 10.07%
            # 6 cuotas -> 15.37%
            # 9 cuotas -> 20.47%
            # 12 cuotas-> 25.87%
            aumento_pct = 0.0
            if cuotas is not None:
                try:
                    cuotas_int = int(cuotas)
                except Exception:
                    cuotas_int = None

                if cuotas_int == 1:
                    aumento_pct = 0.0
                elif cuotas_int == 3:
                    aumento_pct = 10.07
                elif cuotas_int == 6:
                    aumento_pct = 15.37
                elif cuotas_int == 9:
                    aumento_pct = 20.47
                elif cuotas_int == 12:
                    aumento_pct = 25.87
                else:
                    aumento_pct = 0.0

                # Ajustaremos la tasa (tasa_actual) mediante bisección para alcanzar el premio objetivo
                # Si hay un aumento por cuotas, el solver debe buscar el premio antes del aumento
                # (es decir, target_premio dividido por 1 + aumento_pct) para que al aplicar
                # el aumento al final el premio coincida exactamente con target_premio.
                if aumento_pct and aumento_pct != 0.0:
                    effective_target_premio = float(target_premio) / (1.0 + (aumento_pct / 100.0))
                else:
                    effective_target_premio = float(target_premio)

            tasa_original = float(row.tasaAplicada)
            tasa_min, tasa_max = 0.0, max(tasa_original * 10.0, 1000.0)
            tasa_actual = tasa_original

            # Subtotal original (para referencia de impuestos) - usar el recargo financiero de la DB como referencia
            subtotal_orig = prima_tarifa_orig + der_emision_orig + rec_financiero_db + rec_adm_monto

            # Iteración de bisección
            tolerancia = 0.01
            max_iter = 100
            iter_count = 0

            while iter_count < max_iter:
                # Calcular prima tarifa por días
                nueva_prima_tarifa = (tasa_actual * sumaAseg) / 1000 / 365 * dias

                # Recargo administrativo fijo
                nuevo_recargo_adm = nueva_prima_tarifa * (rec_admin_pct / 100)

                # Der. de emisión
                nuevo_der_emision = obtener_derecho(nueva_prima_tarifa)

                # Recargo financiero: usar el monto fijo de la DB (no se modifica por cuotas)
                rec_financiero = rec_financiero_db

                # Subtotal provisorio
                subtotal_base = nueva_prima_tarifa - bonificacion + rec_financiero + nuevo_der_emision + nuevo_recargo_adm + gastos_escribania

                # Impuestos: definir una base imponible clara que incluya
                # la prima tarifa, recargo administrativo y derecho de emisión
                # (excluimos recargo financiero y gastos de escribanía de la base)
                detalle_impuestos = []
                # Base imponible usada para impuestos (antes de aplicar aumento por cuotas)
                base_imponible = nueva_prima_tarifa - bonificacion + nuevo_recargo_adm + nuevo_der_emision
                
                base_ori = 0
                for r in impuestos_rows:
                    if r.Sol2Base == base_ori or base_ori == 0:
                        base_ori = r.Sol2Base
                        ali = float(r.Sol2Ali) if hasattr(r, 'Sol2Ali') else 0.0
                        # Usamos la misma base imponible para todos los impuestos recogidos
                        imp_base = round(base_imponible, 2)
                        imp_importe = round(imp_base * ali / 100.0, 2)
                        detalle_impuestos.append(ImpuestoDetalle(
                            impCod=str(r.ImpCod),
                            base=imp_base,
                            alicuota=ali,
                            importe=imp_importe
                        ))
                    else:
                        # Si la base original no coincide, asignar 0 (caso especial)
                        detalle_impuestos.append(ImpuestoDetalle(
                            impCod=str(r.ImpCod),
                            base=0.0,
                            alicuota=float(r.Sol2Ali) if hasattr(r, 'Sol2Ali') else 0.0,
                            importe=0.0
                        ))

                total_impuestos = round(sum(imp.importe for imp in detalle_impuestos), 2) + base_imponible

                for imp in detalle_impuestos:
                    if imp.base == 0:
                        imp.base = total_impuestos
                        imp.importe = round(imp.base * imp.alicuota / 100.0, 2)
                        total_impuestos += imp.importe


                total_impuestos = round(sum(imp.importe for imp in detalle_impuestos), 2)

                # Premio total (antes del aumento por cuotas)
                nuevo_premio = round(base_imponible + total_impuestos, 2)

                # comparar contra el objetivo efectivo (antes del aumento por cuotas)
                diferencia = nuevo_premio - effective_target_premio
                if abs(diferencia) <= tolerancia:
                    break

                # Ajuste por bisección sobre la tasa
                if nuevo_premio < target_premio:
                    tasa_min = tasa_actual
                    tasa_actual = (tasa_actual + tasa_max) / 2.0
                else:
                    tasa_max = tasa_actual
                    tasa_actual = (tasa_actual + tasa_min) / 2.0

                iter_count += 1

            # Redondeos finales
            nuevo_recargo_adm = nueva_prima_tarifa * (rec_admin_pct / 100)
            # rec_financiero final: usar monto DB (se mantiene fuera del premio)
            rec_financiero = rec_financiero_db

            # Recalcular base imponible final y los impuestos (antes de aumento)
            base_imponible = round(nueva_prima_tarifa - bonificacion + nuevo_recargo_adm + nuevo_der_emision, 2)
            # Recalcular importes de impuestos a partir de la base_imponible

            # Premio (antes del aumento por cuotas)
            nuevo_premio = round(base_imponible + total_impuestos, 2)

            # Si hay aumento por cuotas, aplicarlo proporcionalmente a los componentes
            # (prima, recargo administrativo, derecho e impuestos) para preservar
            # la igualdad: prima + rec_admin + der + impuestos == premio
            if aumento_pct and aumento_pct != 0.0:
                factor = 1.0 + (aumento_pct / 100.0)
                # Escalar componentes
                nueva_prima_tarifa = round(nueva_prima_tarifa * factor, 2)
                nuevo_recargo_adm = round(nuevo_recargo_adm * factor, 2)
                nuevo_der_emision = round(nuevo_der_emision * factor, 2)
                # Recalcular impuestos a partir de la base escalada
                base_imponible = round(nueva_prima_tarifa - bonificacion + nuevo_recargo_adm + nuevo_der_emision, 2)
                total_impuestos = 0.0
                base_ori = 0
                for imp in detalle_impuestos:
                    if imp.base == base_ori or base_ori == 0:
                        base_ori = imp.base
                        imp.base = base_imponible
                        imp.importe = round(imp.base * imp.alicuota / 100.0, 2)
                        total_impuestos += imp.importe
                    else:
                        imp.base = 0.0
                        imp.importe = 0.0
                total_impuestos = round(total_impuestos, 2)
                nuevo_premio = round(base_imponible + total_impuestos, 2)

                for imp in detalle_impuestos:
                    if imp.base == 0:
                        imp.base = nuevo_premio
                        imp.importe = round(imp.base * imp.alicuota / 100.0, 2)
                        total_impuestos += imp.importe

                nuevo_premio = round(base_imponible + total_impuestos, 2)

            recAdministrativoPct = round(rec_admin_pct, 2)
            # Aseguramos enviar el recFinancieroPct final en la respuesta

            # Log del tipo recibido (F/U/C) - no cambia lógica actual
            print(f"Recotizar2 called for app={application_id} tipo={tipo}")

            return QuoteDetails(
                primaTarifa=round(nueva_prima_tarifa, 2),
                bonificacion=0.0,
                bonificacionPct=0.0,
                primaNeta=round(nueva_prima_tarifa - 0.0, 2),
                recAdministrativo=round(nuevo_recargo_adm, 2),
                recAdministrativoPct=recAdministrativoPct,
                recFinanciero=round(rec_financiero, 2),
                recFinancieroPct=round(rec_financiero_pct, 2),
                derEmision=nuevo_der_emision,
                gastosEscribania=gastos_escribania,
                subtotal=round(base_imponible, 2),
                impuestos=total_impuestos,
                premio=nuevo_premio,
                tasaAplicada=tasa_actual if 'tasa_actual' in locals() else tasa,
                sumaAsegurada=sumaAseg,
                detalleImpuestos=detalle_impuestos
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
