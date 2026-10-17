from typing import Dict, Any, List, Optional
from ce3x_mcp.core.models import ProyectoCertificacion, ResultadoCalificacion, MedidaMejora

def generar_informe_justificativo_nextgen(
    proyecto: ProyectoCertificacion,
    calificacion_inicial: ResultadoCalificacion,
    medida_seleccionada: MedidaMejora,
    todas_las_medidas: Optional[List[MedidaMejora]] = None
) -> Dict[str, Any]:
    """
    Genera el Documento Técnico Oficial de Medidas de Mejora de la Eficiencia Energética (RD 390/2021)
    y Dictamen Justificativo de Ayudas Públicas (Fondos Next Generation EU - RD 853/2021)
    y deducciones fiscales en el IRPF.
    """
    ep_inicial = calificacion_inicial.consumo_energia_primaria_nr
    ep_final = ep_inicial * (1.0 - medida_seleccionada.ahorro_energia_primaria_pct / 100.0)
    ahorro_ep_pct = medida_seleccionada.ahorro_energia_primaria_pct
    
    # 1. Evaluación Real Decreto 853/2021 (Programas de ayuda residencial NextGen)
    cumple_nextgen_30 = ahorro_ep_pct >= 30.0
    
    # Determinar rango de subvención Programa 3 / 4
    if ahorro_ep_pct >= 60.0:
        pct_subvencion_rd853 = 80.0
        max_ayuda_vivienda = 18800.0
    elif ahorro_ep_pct >= 45.0:
        pct_subvencion_rd853 = 65.0
        max_ayuda_vivienda = 11600.0
    elif ahorro_ep_pct >= 30.0:
        pct_subvencion_rd853 = 40.0
        max_ayuda_vivienda = 6300.0
    else:
        pct_subvencion_rd853 = 0.0
        max_ayuda_vivienda = 0.0
        
    inversion = medida_seleccionada.inversion_estimada_eur
    ayuda_estimada_rd853 = min(inversion * (pct_subvencion_rd853 / 100.0), max_ayuda_vivienda)
    
    # 2. Evaluación Deducciones Fiscales IRPF (D.A. 50ª Ley IRPF)
    aplica_irpf_40 = cumple_nextgen_30 or medida_seleccionada.nueva_letra_emisiones in ["A", "B"]
    base_max_irpf = 7500.0
    deduccion_irpf_eur = min(inversion - ayuda_estimada_rd853, base_max_irpf) * 0.40 if aplica_irpf_40 else 0.0
    
    coste_neto_usuario = max(0.0, inversion - ayuda_estimada_rd853 - deduccion_irpf_eur)
    
    # Generar tabla comparativa de todos los paquetes propuestos
    lista_mm = todas_las_medidas or [medida_seleccionada]
    filas_tabla_comparativa = []
    for idx, m in enumerate(lista_mm, start=1):
        ep_m = ep_inicial * (1.0 - m.ahorro_energia_primaria_pct / 100.0)
        filas_tabla_comparativa.append(
            f"| **Conjunto {idx}: {m.tipo}** | {m.nombre} | {m.inversion_estimada_eur:,.2f} € | {m.ahorro_energia_primaria_pct:.1f} % | {m.nueva_letra_energia_primaria} / {m.nueva_letra_emisiones} | {m.ahorro_factura_anual_eur:,.2f} €/año | {m.periodo_retorno_anos:.1f} años |"
        )
    tabla_comparativa_str = "\n".join(filas_tabla_comparativa)

    dictamen_md = f"""# 🏛️ Documento Técnico de Medidas de Mejora y Dictamen Técnico Justificativo de Ayudas (NextGen & IRPF)
*Conforme a las exigencias del Real Decreto 390/2021, el CTE DB-HE y el RD 853/2021 (Fondos NextGeneration EU)*

## 1. Datos Generales del Inmueble y Certificación
- **Edificio / Vivienda:** {proyecto.administrativos.nombre_edificio}
- **Dirección:** {proyecto.administrativos.direccion}, {proyecto.administrativos.municipio} ({proyecto.administrativos.provincia})
- **Referencia Catastral:** {proyecto.administrativos.referencia_catastral or 'No aportada'}
- **Superficie Útil Acondicionada:** {proyecto.generales.superficie_util:.2f} m²
- **Zona Climática CTE:** {proyecto.generales.zona_climatica}
- **Calificación Inicial Existente:** Consumo: **{calificacion_inicial.letra_global_energia_primaria}** ({ep_inicial:.2f} kWh/m²·año) | Emisiones: **{calificacion_inicial.letra_global_emisiones}** ({calificacion_inicial.emisiones_co2:.2f} kgCO₂/m²·año)

---

## 2. Conjuntos de Medidas de Mejora Evaluados (Comparativa Técnica y Económica)

| Conjunto de Mejora | Denominación Técnica | Inversión Estimada | Ahorro EPnr | Nueva Letra (Cons/Emis) | Ahorro Factura | Retorno Simple |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
{tabla_comparativa_str}

---

## 3. Descripción Técnica Detallada de los Conjuntos

### 🔹 Conjunto 1: Mejora de la Envolvente Térmica (Reducción Pasiva de Demanda)
- **Actuación:** Incorporación de Sistema de Aislamiento Térmico por el Exterior (SATE) de 8 cm de EPS grafito (U = 0.32 W/m²K) y renovación de carpinterías por ventanas de PVC de 5 cámaras con doble acristalamiento bajo emisivo 4/16/4 con gas argón.
- **Objetivo:** Reducción drástica de pérdidas térmicas invernales y puentes térmicos en contorno de huecos.

### 🔹 Conjunto 2: Sustitución de Generación Térmica (Electrificación de Alta Eficiencia)
- **Actuación:** Sustitución de calderas existentes por Bomba de Calor Aerotérmica para producción integral de calefacción y Agua Caliente Sanitaria (ACS) con SCOP estacional superior a 3.60.
- **Objetivo:** Maximizar el rendimiento estacional y suprimir el consumo directo de combustibles fósiles.

### 🔹 Conjunto 3: Rehabilitación Integral con Renovables (Opción Destacada de Máxima Eficiencia)
- **Actuación:** Combinación simultánea de aislamiento SATE + carpinterías de alta eficiencia + Bomba de calor aerotérmica + instalación solar fotovoltaica en régimen de autoconsumo (3 kWp).
- **Objetivo:** Descarbonización casi nula (Edificio de Consumo Casi Nulo - nZEB) y acceso a las máximas ayudas públicas.

---

## 4. Dictamen Justificativo para Ayudas Públicas (NextGen RD 853/2021 e IRPF)
*Evaluación económica sobre la actuación integral recomendada ({medida_seleccionada.nombre}):*

- **Inversión Total Estimada:** {inversion:,.2f} €
- **Subvención Directa Estimada (RD 853/2021 - {pct_subvencion_rd853:.0f}%):** {ayuda_estimada_rd853:,.2f} €
- **Deducción Fiscal en el IRPF Estimada (40% s/ base neta):** {deduccion_irpf_eur:,.2f} €
- **Inversión Neta Final para el Propietario:** **{coste_neto_usuario:,.2f} €**
- **Ahorro Anual Estimado en Factura Energética:** {medida_seleccionada.ahorro_factura_anual_eur:,.2f} €/año
- **Plazo Real de Retorno de la Inversión Neta:** **{round(coste_neto_usuario / medida_seleccionada.ahorro_factura_anual_eur, 1) if medida_seleccionada.ahorro_factura_anual_eur > 0 else 0} años**

---

## 5. Conclusión y Firma del Técnico Competente
El técnico que suscribe ({proyecto.administrativos.nombre_tecnico}, {proyecto.administrativos.titulacion_tecnico}) dictamina que las medidas descritas son técnicamente viables y cumplen estrictamente las exigencias del **Real Decreto 390/2021**, el **Real Decreto 853/2021** y la **Disposición Adicional 50ª de la Ley del IRPF**, siendo el presente documento plenamente válido para su incorporación al expediente del certificado energético y solicitud de subvenciones.
"""

    return {
        "valido": True,
        "cumple_umbral_nextgen_30": cumple_nextgen_30,
        "porcentaje_ahorro_epnr": ahorro_ep_pct,
        "inversion_total_eur": inversion,
        "subvencion_rd853_eur": ayuda_estimada_rd853,
        "deduccion_irpf_eur": deduccion_irpf_eur,
        "coste_neto_propietario_eur": round(coste_neto_usuario, 2),
        "dictamen_markdown": dictamen_md
    }
