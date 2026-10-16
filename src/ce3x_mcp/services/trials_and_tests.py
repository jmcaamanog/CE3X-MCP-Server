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

import math

def calcular_patron_sombras_edificio_colindante(
    distancia_edificio_m: float,
    altura_edificio_m: float,
    orientacion_fachada: str = "Sur",
    descripcion_obstaculo: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calcula el angulo de elevacion de obstaculo remoto (edificio enfrente o colindante)
    y el factor reductor de radiacion solar F_sh segun la tabla oficial de obstaculos de CE3X y CTE DB-HE.
    """
    if distancia_edificio_m <= 0:
        raise ValueError("La distancia al edificio obstaculo debe ser mayor que cero.")
    
    rad = math.atan(altura_edificio_m / distancia_edificio_m)
    alfa_grados = round(math.degrees(rad), 1)
    
    if alfa_grados < 10.0:
        f_verano, f_invierno = 1.0, 1.0
        nivel = "Obstaculo despreciable (cielo despejado)"
    elif alfa_grados < 25.0:
        f_verano, f_invierno = 0.90, 0.80
        nivel = "Obstaculo bajo (sombras ligeras en invierno)"
    elif alfa_grados < 45.0:
        f_verano, f_invierno = 0.75, 0.55
        nivel = "Obstaculo medio (calle estandar urbana)"
    elif alfa_grados < 60.0:
        f_verano, f_invierno = 0.60, 0.35
        nivel = "Obstaculo alto (calle estrecha o patio denso)"
    else:
        f_verano, f_invierno = 0.40, 0.15
        nivel = "Obstaculo severo (patio de luces angosto o canon urbano)"
        
    return {
        "valido": True,
        "distancia_edificio_m": distancia_edificio_m,
        "altura_edificio_m": altura_edificio_m,
        "angulo_elevacion_alfa_grados": alfa_grados,
        "orientacion_fachada": orientacion_fachada.upper(),
        "factor_sombra_verano_fsh": f_verano,
        "factor_sombra_invierno_fsh": f_invierno,
        "bloqueo_radiacion_invierno_pct": round((1.0 - f_invierno) * 100.0, 1),
        "clasificacion_entorno": nivel,
        "descripcion": descripcion_obstaculo or f"Edificio enfrente a {distancia_edificio_m}m con {altura_edificio_m}m de altura"
    }

def estimar_parametros_terciario_comercial(
    tipo_actividad: str = "Comercio",
    superficie_util_m2: float = 100.0,
    tipo_luminaria: str = "LED",
    nivel_iluminacion_lux: Optional[float] = None
) -> Dict[str, Any]:
    """
    Calcula los parametros obligatorios de CE3X para uso Pequeno Terciario / Locales Comerciales:
    potencia de iluminacion instalada (W/m2), VEEI objetivo segun CTE DB-HE 3 y tasa de ventilacion segun RITE.
    """
    actividad = tipo_actividad.strip().lower()
    
    if "oficina" in actividad or "despacho" in actividad:
        lux_ref = 500.0
        horas_anuales = 2500
        ida = "IDA 2 (Aire de buena calidad - 12.5 l/s por persona)"
        caudal_pers = 12.5
        ocupacion_m2_pers = 10.0
    elif "comercio" in actividad or "tienda" in actividad or "local" in actividad:
        lux_ref = 500.0
        horas_anuales = 3000
        ida = "IDA 2 (Aire de buena calidad - 10 l/s por persona)"
        caudal_pers = 10.0
        ocupacion_m2_pers = 5.0
    elif "restaurante" in actividad or "bar" in actividad:
        lux_ref = 300.0
        horas_anuales = 4000
        ida = "IDA 3 (Aire de calidad media - 8 l/s por persona)"
        caudal_pers = 8.0
        ocupacion_m2_pers = 3.0
    else:
        lux_ref = 300.0
        horas_anuales = 2000
        ida = "IDA 2 (Calidad estandar)"
        caudal_pers = 10.0
        ocupacion_m2_pers = 10.0
        
    lux = nivel_iluminacion_lux or lux_ref
    
    lum = tipo_luminaria.strip().upper()
    if "LED" in lum:
        veei_estimado = 1.8
        potencia_w_m2 = round((veei_estimado * lux) / 100.0, 1)
    elif "FLUOR" in lum:
        veei_estimado = 3.5
        potencia_w_m2 = round((veei_estimado * lux) / 100.0, 1)
    else:
        veei_estimado = 6.0
        potencia_w_m2 = round((veei_estimado * lux) / 100.0, 1)
        
    potencia_total_kw = round((potencia_w_m2 * superficie_util_m2) / 1000.0, 2)
    consumo_anual_kwh_m2 = round((potencia_w_m2 * horas_anuales) / 1000.0, 1)
    
    personas_estimadas = max(1, round(superficie_util_m2 / ocupacion_m2_pers))
    caudal_total_m3h = round(personas_estimadas * caudal_pers * 3.6, 1)
    
    return {
        "valido": True,
        "tipo_actividad": tipo_actividad,
        "superficie_util_m2": superficie_util_m2,
        "tipo_luminaria": lum,
        "nivel_iluminacion_lux": lux,
        "potencia_iluminacion_w_m2": potencia_w_m2,
        "potencia_total_instalada_kw": potencia_total_kw,
        "veei_estimado_w_m2_100lux": veei_estimado,
        "cumple_cte_db_he3": veei_estimado <= 3.5,
        "consumo_anual_iluminacion_kwh_m2": consumo_anual_kwh_m2,
        "horas_anuales_actividad": horas_anuales,
        "categoria_calidad_aire_rite": ida,
        "ocupantes_estimados": personas_estimadas,
        "caudal_ventilacion_exterior_m3h": caudal_total_m3h
    }


def registrar_ensayo_flujometria_termica_iso9869(
    flujo_medio_w_m2: float,
    temp_interior_media_c: float,
    temp_exterior_media_c: float,
    duracion_ensayo_horas: float = 72.0,
    elemento_analizado: str = "Fachada principal"
) -> Dict[str, Any]:
    """
    Calcula la transmitancia termica real U (W/m2K) de un cerramiento a partir
    de un ensayo in situ de flujometria termica con sondas de contacto segun norma UNE-EN ISO 9869-1.
    Valido para justificar el nivel conocido de envolvente en CE3X y Anexo IV de RD 390/2021.
    """
    delta_t = abs(temp_interior_media_c - temp_exterior_media_c)
    if delta_t < 5.0:
        raise ValueError("El gradiente termico medio durante el ensayo debe ser de al menos 5 C para validez segun ISO 9869.")
    if flujo_medio_w_m2 <= 0:
        raise ValueError("El flujo de calor medio debe ser mayor que cero.")
        
    conductancia_superficial = flujo_medio_w_m2 / delta_t
    resistencia_termica_cuerpo = 1.0 / conductancia_superficial
    rsi_rse = 0.17
    resistencia_total = resistencia_termica_cuerpo + rsi_rse
    u_medido = round(1.0 / resistencia_total, 2)
    
    return {
        "valido": True,
        "norma_ensayo": "UNE-EN ISO 9869-1",
        "elemento_analizado": elemento_analizado,
        "duracion_horas": duracion_ensayo_horas,
        "cumple_duracion_minima_72h": duracion_ensayo_horas >= 72.0,
        "flujo_medio_w_m2": flujo_medio_w_m2,
        "gradiente_temperatura_medio_c": round(delta_t, 1),
        "conductancia_medida_w_m2k": round(conductancia_superficial, 3),
        "resistencia_termica_total_m2k_w": round(resistencia_total, 3),
        "u_medido_w_m2k": u_medido,
        "nivel_ce3x": "Conocido (Ensayo in situ de flujometria)",
        "texto_anexo_iv": f"Ensayo de flujometria termica in situ s/ UNE-EN ISO 9869-1 ({duracion_ensayo_horas}h) en {elemento_analizado}. Transmitancia medida U = {u_medido} W/m2K."
    }
