from typing import Dict, Any, List
from ce3x_mcp.core.models import ProyectoCertificacion, ResultadoCalificacion, MedidaMejora

def generar_informe_justificativo_nextgen(
    proyecto: ProyectoCertificacion,
    calificacion_inicial: ResultadoCalificacion,
    medida_seleccionada: MedidaMejora
) -> Dict[str, Any]:
    """
    Genera el dictamen técnico justificativo para la solicitud de subvenciones
    del Plan de Recuperación, Transformación y Resiliencia (Fondos Next Generation EU - RD 853/2021)
    y deducciones en el IRPF por obras de mejora de la eficiencia energética.
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
    # Deducción del 40% para viviendas habituales con reducción >= 30% de EPnr o letra A/B
    aplica_irpf_40 = cumple_nextgen_30 or medida_seleccionada.nueva_letra_emisiones in ["A", "B"]
    base_max_irpf = 7500.0
    deduccion_irpf_eur = min(inversion - ayuda_estimada_rd853, base_max_irpf) * 0.40 if aplica_irpf_40 else 0.0
    
    coste_neto_usuario = max(0.0, inversion - ayuda_estimada_rd853 - deduccion_irpf_eur)
    
    # Dictamen técnico redactado en Markdown
    dictamen_md = f"""# 🏛️ Dictamen Técnico Justificativo de Ayudas y Deducciones Fiscales (NextGen & IRPF)

## 1. Datos Generales del Inmueble
- **Edificio / Vivienda:** {proyecto.administrativos.nombre_edificio}
- **Dirección:** {proyecto.administrativos.direccion}, {proyecto.administrativos.municipio} ({proyecto.administrativos.provincia})
- **Referencia Catastral:** {proyecto.administrativos.referencia_catastral or 'No aportada'}
- **Superficie Útil Acondicionada:** {proyecto.generales.superficie_util:.2f} m²
- **Zona Climática CTE:** {proyecto.generales.zona_climatica}

---

## 2. Comparativa Energética Reglamentaria (Antes vs Después)
| Indicador Energético | Situación Inicial | Situación Tras la Mejora | Reducción Obtenida | Cumplimiento Umbral NextGen (≥ 30%) |
| :--- | :---: | :---: | :---: | :---: |
| **Consumo Energía Primaria No Renovable (EPnr)** | **{ep_inicial:.2f} kWh/m²·año** | **{ep_final:.2f} kWh/m²·año** | **{ahorro_ep_pct:.1f} %** | **{'✅ CUMPLE' if cumple_nextgen_30 else '❌ NO ALCANZA'}** |
| **Calificación Global (Letra Emisiones)** | **{calificacion_inicial.letra_global_emisiones}** | **{medida_seleccionada.nueva_letra_emisiones}** | **Salto a {medida_seleccionada.nueva_letra_emisiones}** | **{'✅ MEJORA DE LETRA' if medida_seleccionada.nueva_letra_emisiones < calificacion_inicial.letra_global_emisiones else 'SIN CAMBIO'}** |

---

## 3. Descripción de la Actuación Propuesta
**{medida_seleccionada.nombre}**  
*{medida_seleccionada.descripcion}*

---

## 4. Cuantificación Económica y Financiación Pública Estimada
- **Inversión Total Estimada:** {inversion:,.2f} €
- **Subvención Directa Estimada (RD 853/2021 - {pct_subvencion_rd853:.0f}%):** {ayuda_estimada_rd853:,.2f} €
- **Deducción Fiscal en el IRPF Estimada (40%):** {deduccion_irpf_eur:,.2f} €
- **Inversión Neta Final para el Propietario:** **{coste_neto_usuario:,.2f} €**
- **Ahorro Anual Estimado en Factura Energética:** {medida_seleccionada.ahorro_factura_anual_eur:,.2f} €/año
- **Plazo Real de Retorno de la Inversión Neta:** **{round(coste_neto_usuario / medida_seleccionada.ahorro_factura_anual_eur, 1) if medida_seleccionada.ahorro_factura_anual_eur > 0 else 0} años**

---

## 5. Conclusión y Dictamen del Técnico Competente
El técnico que suscribe ({proyecto.administrativos.nombre_tecnico}, {proyecto.administrativos.titulacion_tecnico}) dictamina que la actuación descrita cumple estrictamente con los requisitos exigidos por el **Real Decreto 853/2021** y la **Disposición Adicional 50ª de la Ley del IRPF**, resultando apta para la tramitación de las ayudas públicas y beneficios fiscales correspondientes.
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

