"""
Módulo oficial de datos climáticos CTE DB-HE, factores de paso IDAE
y motor de cálculo de demandas y consumos conectado con las escalas oficiales de CE3X v3.2.
"""

from typing import Dict, Any, List, Tuple, Optional
from ce3x_mcp.services.ce3x_engine_connector import obtener_escalas_oficiales_zona, asignar_letra_segun_limites

# Factores de paso oficiales del IDAE / MITERD (Actualización vigente)
FACTORES_PASO = {
    "Electricidad": {
        "f_ep_nr": 1.954,   # kWh EPnr / kWh EF
        "f_co2": 0.331      # kg CO2 / kWh EF
    },
    "GasNatural": {
        "f_ep_nr": 1.195,
        "f_co2": 0.252
    },
    "Gasoleo": {
        "f_ep_nr": 1.179,
        "f_co2": 0.311
    },
    "BiomasaPellet": {
        "f_ep_nr": 0.085,
        "f_co2": 0.018
    },
    "GLP": {
        "f_ep_nr": 1.201,
        "f_co2": 0.254
    }
}

# Tabla simplificada de zonas climáticas de capitales de provincia de referencia (CTE DB-HE)
ZONAS_CAPITALES: Dict[str, str] = {
    "A Coruña": "C1",
    "Lugo": "D1",
    "Ourense": "C2",
    "Pontevedra": "C1",
    "Madrid": "D3",
    "Barcelona": "C2",
    "Valencia": "B3",
    "Sevilla": "B4",
    "Málaga": "A3",
    "Zaragoza": "D3",
    "Bilbao": "C1",
    "Valladolid": "D2",
    "Oviedo": "D1",
    "Santander": "C1",
    "Burgos": "E1",
    "Granada": "D3",
    "Toledo": "C3",
    "Palma de Mallorca": "B3",
    "Las Palmas de Gran Canaria": "alpha3",
    "Santa Cruz de Tenerife": "alpha3"
}

# Transmitancias U por defecto (W/m²K) según periodo normativo y zona (Manual Fundamentos CE3X)
U_DEFECTO_FACHADA: Dict[str, float] = {
    "Anterior1979": 1.80,
    "NBE_CT_79": 1.20,
    "CTE_2006": 0.66,
    "CTE_2013": 0.45,
    "CTE_2019": 0.35
}

U_DEFECTO_CUBIERTA: Dict[str, float] = {
    "Anterior1979": 2.20,
    "NBE_CT_79": 1.10,
    "CTE_2006": 0.45,
    "CTE_2013": 0.35,
    "CTE_2019": 0.28
}

U_DEFECTO_HUECO: Dict[str, float] = {
    "Anterior1979": 5.70,   # Vidrio simple marco metálico sin RPT
    "NBE_CT_79": 3.80,      # Vidrio simple marco madera o doble básico
    "CTE_2006": 2.80,       # Doble estándar marco con RPT
    "CTE_2013": 2.20,       # Doble con cámara 12mm
    "CTE_2019": 1.60        # Doble bajo emisivo PVC/RPT
}

def obtener_zona_climatica(provincia: str, municipio: str, altitud_m: float = 0.0) -> str:
    """
    Determina la zona climática CTE según la provincia y corrección por altitud.
    """
    prov_limpia = provincia.strip().title()
    for cap, zona in ZONAS_CAPITALES.items():
        if cap.lower() in prov_limpia.lower() or prov_limpia.lower() in cap.lower():
            if altitud_m > 800 and zona.startswith("D"):
                return "E1"
            return zona
    return "C1"

def estimar_transmitancias_por_ano(ano: int, zona_climatica: str) -> Dict[str, float]:
    """
    Estima las transmitancias térmicas por defecto según el año de construcción.
    """
    if ano < 1979:
        norma = "Anterior1979"
    elif ano < 2006:
        norma = "NBE_CT_79"
    elif ano < 2013:
        norma = "CTE_2006"
    elif ano < 2019:
        norma = "CTE_2013"
    else:
        norma = "CTE_2019"
        
    return {
        "normativa": norma,
        "u_fachada": U_DEFECTO_FACHADA[norma],
        "u_cubierta": U_DEFECTO_CUBIERTA[norma],
        "u_hueco": U_DEFECTO_HUECO[norma]
    }

def calcular_calificacion_energetica_simplificada(
    superficie_util: float,
    ano_construccion: int,
    zona_climatica: str = "C1",
    tipo_calefaccion: Optional[str] = None,
    tipo_acs: Optional[str] = None,
    tipologia: str = "Bloque"
) -> Dict[str, Any]:
    """
    Calcula la demanda energética estimada, consumo de energía primaria no renovable,
    emisiones de CO2 y asigna las letras de calificación energética oficiales (A a G)
    conectando con la base de datos de escalas y edificios de referencia de CE3X (Localidades.xml).
    """
    # Cargar escalas oficiales de CE3X para la zona y tipología
    escalas = obtener_escalas_oficiales_zona(zona_climatica, tipologia)
    ref = escalas.get("edificio_referencia_existente", {})
    
    trans = estimar_transmitancias_por_ano(ano_construccion, zona_climatica)
    
    # Demanda de referencia oficial de CE3X
    demanda_cal_ref = float(ref.get("DemandaCalefaccion", 80.0))
    demanda_ref_ref = float(ref.get("DemandaRefrigeracion", 0.0))
    demanda_acs_ref = float(ref.get("DemandaACS", 15.0))
    
    # Ajuste de la demanda según transmitancia del edificio frente a NBE-CT-79 (1.20 W/m²K)
    factor_envolvente = trans["u_fachada"] / 1.20
    demanda_cal = round(demanda_cal_ref * (0.35 + 0.65 * factor_envolvente), 2)
    demanda_ref = round(demanda_ref_ref * (0.50 + 0.50 * factor_envolvente), 2)
    demanda_acs = round(demanda_acs_ref, 2)
    
    # Detección de instalaciones especificadas vs defecto
    instalaciones_especificadas = bool(tipo_calefaccion or tipo_acs)
    tc = tipo_calefaccion or "CalderaGasConvencional"
    ta = tipo_acs or "CalderaGasConvencional"
    
    # Rendimiento de calefacción
    tc_low = tc.lower()
    if "aerotermia" in tc_low or "bombadecalor" in tc_low:
        rend_cal = 3.2
        comb_cal = "Electricidad"
    elif "condensacion" in tc_low:
        rend_cal = 0.95
        comb_cal = "GasNatural" if "gasoleo" not in tc_low else "Gasoleo"
    elif "gasoleo" in tc_low:
        rend_cal = 0.78
        comb_cal = "Gasoleo"
    elif "biomasa" in tc_low:
        rend_cal = 0.85
        comb_cal = "BiomasaPellet"
    elif "joule" in tc_low or "electr" in tc_low:
        rend_cal = 1.0
        comb_cal = "Electricidad"
    else:
        rend_cal = 0.80
        comb_cal = "GasNatural"
        
    # Rendimiento de ACS
    ta_low = ta.lower()
    if "aerotermia" in ta_low or "bombadecalor" in ta_low:
        rend_acs = 2.8
        comb_acs = "Electricidad"
    elif "condensacion" in ta_low:
        rend_acs = 0.90
        comb_acs = "GasNatural" if "gasoleo" not in ta_low else "Gasoleo"
    elif "gasoleo" in ta_low:
        rend_acs = 0.75
        comb_acs = "Gasoleo"
    elif "joule" in ta_low or "termo" in ta_low or "electr" in ta_low:
        rend_acs = 1.0
        comb_acs = "Electricidad"
    else:
        rend_acs = 0.78
        comb_acs = "GasNatural"
        
    seer_ref = 2.5
    
    consumo_cal = demanda_cal / rend_cal
    consumo_acs = demanda_acs / rend_acs
    consumo_ref = (demanda_ref / seer_ref) if demanda_ref > 0 else 0.0
    
    fp_epnr_cal = FACTORES_PASO[comb_cal]["f_ep_nr"]
    fp_co2_cal = FACTORES_PASO[comb_cal]["f_co2"]
    
    fp_epnr_acs = FACTORES_PASO[comb_acs]["f_ep_nr"]
    fp_co2_acs = FACTORES_PASO[comb_acs]["f_co2"]
    
    fp_epnr_elec = FACTORES_PASO["Electricidad"]["f_ep_nr"]
    fp_co2_elec = FACTORES_PASO["Electricidad"]["f_co2"]
    
    epnr_cal = consumo_cal * fp_epnr_cal
    co2_cal = consumo_cal * fp_co2_cal
    
    epnr_acs = consumo_acs * fp_epnr_acs
    co2_acs = consumo_acs * fp_co2_acs
    
    epnr_ref = consumo_ref * fp_epnr_elec
    co2_ref = consumo_ref * fp_co2_elec
    
    epnr_tot = round(epnr_cal + epnr_acs + epnr_ref, 2)
    co2_tot = round(co2_cal + co2_acs + co2_ref, 2)
    
    letra_co2 = asignar_letra_segun_limites(co2_tot, escalas["limites_emisiones"])
    letra_epnr = asignar_letra_segun_limites(epnr_tot, escalas["limites_energia_primaria_no_renovable"])
    letra_cal = asignar_letra_segun_limites(demanda_cal, escalas["limites_demanda_calefaccion"])
    
    aviso_instalaciones = None
    if not instalaciones_especificadas:
        aviso_instalaciones = (
            "AVISO TÉCNICO: No se especificaron equipos de calefacción ni ACS. "
            "Se evaluó la instalación reglamentaria por defecto para edificios existentes según el procedimiento oficial de CE3X. "
            "Para un dictamen definitivo es preceptivo contrastar los equipos reales durante la inspección presencial."
        )

    return {
        "valido": True,
        "zona_climatica": zona_climatica,
        "tipologia": tipologia,
        "superficie_util_m2": superficie_util,
        "ano_construccion": ano_construccion,
        "demandas": {
            "calefaccion": demanda_cal,
            "refrigeracion": demanda_ref,
            "acs": demanda_acs
        },
        "consumo_energia_final": {
            "calefaccion": round(consumo_cal, 2),
            "refrigeracion": round(consumo_ref, 2),
            "acs": round(consumo_acs, 2)
        },
        "consumo_epnr_kwh_m2_ano": epnr_tot,
        "emisiones_co2_kg_m2_ano": co2_tot,
        "calificacion": {
            "emisiones": letra_co2,
            "energia_primaria_no_renovable": letra_epnr,
            "demanda_calefaccion": letra_cal
        },
        # Claves planas de compatibilidad directa
        "demanda_calefaccion_kwh_m2": demanda_cal,
        "demanda_refrigeracion_kwh_m2": demanda_ref,
        "demanda_acs_kwh_m2": demanda_acs,
        "consumo_epnr_totales_kwh_m2": epnr_tot,
        "emisiones_totales_kgco2_m2": co2_tot,
        "calificacion_global_emisiones": letra_co2,
        "calificacion_global_consumo": letra_epnr,
        "letra_calefaccion": letra_cal,
        "letra_consumo": letra_epnr,
        "letra_emisiones": letra_co2,
        "escalas_oficiales": {
            "limites_emisiones": escalas["limites_emisiones"],
            "limites_epnr": escalas["limites_energia_primaria_no_renovable"],
            "fuente": "Escala/Localidades.xml oficial de CE3X v3.2"
        },
        "instalaciones_evaluadas": {
            "calefaccion": tc,
            "combustible_calefaccion": comb_cal,
            "rendimiento_calefaccion": rend_cal,
            "acs": ta,
            "combustible_acs": comb_acs,
            "rendimiento_acs": rend_acs,
            "especificadas_por_usuario": instalaciones_especificadas
        },
        "aviso_normativo": aviso_instalaciones
    }
