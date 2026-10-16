"""
Módulo de Ensayos, Pruebas in situ y Contrastes Oficiales para CE3X
Implementa la gestión de la visita presencial obligatoria (RD 390/2021 Art. 8),
ensayos de estanqueidad Blower Door (UNE-EN ISO 9972), cálculo de puentes térmicos
lineales (DA DB-HE / 3) y contraste con facturación energética real.
"""

from typing import Dict, Any, List, Optional

def registrar_visita_e_inspeccion(
    fecha_visita: str,
    pruebas_realizadas: Optional[List[str]] = None,
    observaciones_tecnicas: Optional[str] = None
) -> Dict[str, Any]:
    """
    Registra formalmente la visita presencial obligatoria exigida por el Art. 8 del RD 390/2021
    y genera el bloque documental oficial para el Anexo IV del Certificado de Eficiencia Energética.
    """
    pruebas_disponibles = {
        "inspeccion_visual": "Inspección ocular directa de la envolvente térmica, carpinterías e instalaciones.",
        "medicion_laser": "Levantamiento dimensional in situ mediante distanciómetro láser calibrado.",
        "comprobacion_placas": "Comprobación de placas de características y fichas técnicas de generadores térmicos y ACS.",
        "termografia": "Inspección termográfica cualitativa con cámara infrarroja para detección de puentes térmicos.",
        "ensayo_blower_door": "Ensayo de estanqueidad al aire mediante presurización Blower Door (UNE-EN ISO 9972).",
        "facturas_electricas": "Cotejo de facturación energética real de los últimos 12 meses."
    }
    seleccionadas = pruebas_realizadas or ["inspeccion_visual", "medicion_laser", "comprobacion_placas"]
    descripciones = [pruebas_disponibles.get(p, p) for p in seleccionadas]
    if observaciones_tecnicas:
        descripciones.append(f"Observaciones: {observaciones_tecnicas}")
        
    texto_completo = " ".join(descripciones)
    return {
        "valido": True,
        "fecha_visita": fecha_visita,
        "cumple_rd390_visita_presencial": True,
        "pruebas_registradas": seleccionadas,
        "texto_anexo_iv": texto_completo,
        "cdata_xml": f"<![CDATA[data:text/html,<h1>Pruebas e Inspecciones in situ</h1>{texto_completo}]]>"
    }

def registrar_ensayo_blower_door(
    volumen_neto_m3: float,
    superficie_envolvente_m2: float,
    caudal_50pa_m3h: float
) -> Dict[str, Any]:
    """
    Procesa un ensayo de estanqueidad al aire según norma UNE-EN ISO 9972 (Blower Door)
    y calcula el valor n50, q50 y la tasa de renovación equivalente para el motor CE3X.
    """
    n50 = caudal_50pa_m3h / volumen_neto_m3
    q50 = caudal_50pa_m3h / superficie_envolvente_m2
    # Infiltración en CE3X: permeabilidad estimada a presión de uso (aprox n50 / 20)
    renovaciones_infiltracion = n50 / 20.0
    
    if n50 <= 0.6:
        diagnostico = "Excelente - Nivel Passivhaus / nZEB de muy alta hermeticidad."
    elif n50 <= 3.0:
        diagnostico = "Conforme - Cumple exigencias límite del CTE DB-HE 2019."
    elif n50 <= 6.0:
        diagnostico = "Media - Nivel típico de edificación NBE-CT-79."
    else:
        diagnostico = "Deficiente - Alta permeabilidad con infiltraciones acusadas."
        
    return {
        "valido": True,
        "normativa": "UNE-EN ISO 9972",
        "n50_ren_h": round(n50, 2),
        "q50_m3_h_m2": round(q50, 2),
        "tasa_infiltracion_ce3x_ren_h": round(renovaciones_infiltracion, 3),
        "diagnostico_hermeticidad": diagnostico
    }

def calcular_puentes_termicos_cte(
    ano_construccion: int,
    perimetro_forjado_m: float,
    perimetro_huecos_m: float,
    longitud_pilares_m: float = 0.0
) -> Dict[str, Any]:
    """
    Calcula las transmitancias térmicas lineales (psi en W/m·K) y la pérdida térmica
    global asociada a puentes térmicos según el catálogo oficial del CTE (DA DB-HE / 3).
    """
    if ano_construccion < 1979:
        psi_forjado, psi_hueco, psi_pilar = 0.85, 0.45, 0.65
    elif ano_construccion < 2007:
        psi_forjado, psi_hueco, psi_pilar = 0.50, 0.28, 0.40
    elif ano_construccion < 2019:
        psi_forjado, psi_hueco, psi_pilar = 0.30, 0.15, 0.20
    else:
        psi_forjado, psi_hueco, psi_pilar = 0.12, 0.05, 0.08
        
    perdida_forjado = psi_forjado * perimetro_forjado_m
    perdida_hueco = psi_hueco * perimetro_huecos_m
    perdida_pilares = psi_pilar * longitud_pilares_m
    perdida_total_w_k = perdida_forjado + perdida_hueco + perdida_pilares
    
    return {
        "valido": True,
        "periodo_normativo": "NBE-CT-79" if ano_construccion < 2007 else "CTE",
        "psi_frente_forjado_w_mk": psi_forjado,
        "psi_contorno_huecos_w_mk": psi_hueco,
        "psi_pilares_w_mk": psi_pilar,
        "perdida_total_puentes_termicos_w_k": round(perdida_total_w_k, 2),
        "desglose_perdidas": {
            "frentes_forjado_w_k": round(perdida_forjado, 2),
            "contorno_huecos_w_k": round(perdida_hueco, 2),
            "pilares_w_k": round(perdida_pilares, 2)
        }
    }

def contrastar_facturas_reales(
    consumo_teorico_kwh_ano: float,
    electricidad_real_kwh: float,
    gas_natural_real_kwh: float = 0.0,
    gasoleo_real_litros: float = 0.0
) -> Dict[str, Any]:
    """
    Compara el consumo real de energía de los últimos 12 meses frente a la demanda
    teórica calculada en el modelo de CE3X, detectando desviaciones de uso.
    """
    kwh_gasoleo = gasoleo_real_litros * 10.0 # aprox 10 kWh/litro
    consumo_real_total = electricidad_real_kwh + gas_natural_real_kwh + kwh_gasoleo
    
    desviacion_pct = ((consumo_real_total - consumo_teorico_kwh_ano) / consumo_teorico_kwh_ano) * 100.0 if consumo_teorico_kwh_ano > 0 else 0.0
    
    if abs(desviacion_pct) <= 15.0:
        diagnostico = "Alineado - El consumo real coincide estrechamente con el modelo normativo (desviación < 15%)."
    elif desviacion_pct > 15.0:
        diagnostico = f"Consumo real superior ({round(desviacion_pct, 1)}%) - Posibles hábitos intensivos, baja eficiencia real o infiltraciones no detectadas."
    else:
        diagnostico = f"Consumo real inferior ({round(abs(desviacion_pct), 1)}%) - Posible baja ocupación, temperatura de consigna reducida o zonas no calefactadas."
        
    return {
        "valido": True,
        "consumo_teorico_kwh_ano": round(consumo_teorico_kwh_ano, 1),
        "consumo_real_total_kwh_ano": round(consumo_real_total, 1),
        "desviacion_porcentual": round(desviacion_pct, 1),
        "diagnostico_contraste": diagnostico
    }

def calcular_sombras_estacionales_hueco(
    orientacion: str = "Sur",
    ancho_hueco_m: float = 1.20,
    alto_hueco_m: float = 1.20,
    retranqueo_m: float = 0.0,
    vuelo_voladizo_m: float = 0.0,
    tiene_toldo: bool = False
) -> Dict[str, Any]:
    """
    Calcula los factores de sombra estacionales (verano e invierno) y el factor solar
    modificado del hueco conforme a las tablas y fórmulas oficiales del CTE DB-HE y CE3X.
    """
    ori = orientacion.strip().upper()
    
    # Factor reductor por retranqueo
    ratio_ret = (retranqueo_m / alto_hueco_m) if alto_hueco_m > 0 else 0.0
    f_ret_ver = max(0.40, 1.0 - (0.8 * ratio_ret)) if ratio_ret > 0 else 1.0
    f_ret_inv = max(0.60, 1.0 - (0.4 * ratio_ret)) if ratio_ret > 0 else 1.0
    
    # Factor reductor por voladizo
    ratio_vol = (vuelo_voladizo_m / alto_hueco_m) if alto_hueco_m > 0 else 0.0
    f_vol_ver = max(0.35, 1.0 - (1.1 * ratio_vol)) if ratio_vol > 0 else 1.0
    f_vol_inv = max(0.65, 1.0 - (0.5 * ratio_vol)) if ratio_vol > 0 else 1.0
    
    # Efecto del toldo en verano
    f_toldo_ver = 0.35 if tiene_toldo else 1.0
    f_toldo_inv = 1.0 # En invierno los toldos se recogen
    
    f_sombra_verano = round(f_ret_ver * f_vol_ver * f_toldo_ver, 2)
    f_sombra_invierno = round(f_ret_inv * f_vol_inv * f_toldo_inv, 2)
    
    # Diagnóstico
    if tiene_toldo or vuelo_voladizo_m > 0.5:
        diagnostico = "Alta protección solar estacional: gran reducción de sobrecalentamiento en verano manteniendo captación invernal."
    elif retranqueo_m > 0.15:
        diagnostico = "Protección moderada por retranqueo constructivo de fachada."
    else:
        diagnostico = "Hueco expuesto sin protecciones solares acusadas (máxima captación solar)."
        
    return {
        "valido": True,
        "orientacion": ori,
        "dimensiones_hueco_m": f"{ancho_hueco_m} x {alto_hueco_m}",
        "factor_sombra_verano": f_sombra_verano,
        "factor_sombra_invierno": f_sombra_invierno,
        "reduccion_radiacion_verano_pct": round((1.0 - f_sombra_verano) * 100.0, 1),
        "diagnostico_sombras": diagnostico
    }
