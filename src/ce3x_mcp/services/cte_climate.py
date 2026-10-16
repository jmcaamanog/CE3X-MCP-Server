from typing import Dict, Any, List, Tuple

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
            # Si altitud es superior a 800m y estamos en zona C o D, puede subir un escalón
            if altitud_m > 800 and zona.startswith("D"):
                return "E1"
            return zona
    # Por defecto para península si no se encuentra
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
    tipo_calefaccion: str = "EfectoJoule",
    tipo_acs: str = "EfectoJoule"
) -> Dict[str, Any]:
    """
    Calcula la demanda energética estimada, consumo de energía primaria no renovable,
    emisiones de CO2 y asigna las letras de calificación energética (A a G).
    """
    trans = estimar_transmitancias_por_ano(ano_construccion, zona_climatica)
    
    factor_zona = 1.4 if zona_climatica.startswith("D") else (1.8 if zona_climatica.startswith("E") else 1.0)
    demanda_cal = trans["u_fachada"] * 45.0 * factor_zona
    demanda_ref = 15.0 if not zona_climatica.endswith("4") else 30.0
    demanda_acs = 22.0
    
    rend_cal = 3.2 if "aerotermia" in tipo_calefaccion.lower() or "bombadecalor" in tipo_calefaccion.lower() else (0.92 if "condensacion" in tipo_calefaccion.lower() else 1.0)
    rend_acs = 2.8 if "aerotermia" in tipo_acs.lower() or "bombadecalor" in tipo_acs.lower() else (0.90 if "condensacion" in tipo_acs.lower() else 1.0)
    
    consumo_cal = demanda_cal / rend_cal
    consumo_acs = demanda_acs / rend_acs
    consumo_ref = demanda_ref / 2.5
    
    fp_epnr = FACTORES_PASO["Electricidad"]["f_ep_nr"] if "joule" in tipo_calefaccion.lower() or "aerotermia" in tipo_calefaccion.lower() else FACTORES_PASO["GasNatural"]["f_ep_nr"]
    fp_co2 = FACTORES_PASO["Electricidad"]["f_co2"] if "joule" in tipo_calefaccion.lower() or "aerotermia" in tipo_calefaccion.lower() else FACTORES_PASO["GasNatural"]["f_co2"]
    
    epnr_tot = (consumo_cal + consumo_acs + consumo_ref) * fp_epnr
    co2_tot = (consumo_cal + consumo_acs + consumo_ref) * fp_co2
    
    # Asignacion de escala
    if co2_tot < 6.8:
        letra_co2 = "A"
    elif co2_tot < 11.2:
        letra_co2 = "B"
    elif co2_tot < 18.2:
        letra_co2 = "C"
    elif co2_tot < 28.5:
        letra_co2 = "D"
    elif co2_tot < 44.2:
        letra_co2 = "E"
    elif co2_tot < 54.3:
        letra_co2 = "F"
    else:
        letra_co2 = "G"
        
    return {
        "demanda_calefaccion_kwh_m2": round(demanda_cal, 2),
        "demanda_refrigeracion_kwh_m2": round(demanda_ref, 2),
        "demanda_acs_kwh_m2": round(demanda_acs, 2),
        "consumo_epnr_totales_kwh_m2": round(epnr_tot, 2),
        "emisiones_calefaccion_kgco2_m2": round(consumo_cal * fp_co2, 2),
        "emisiones_refrigeracion_kgco2_m2": round(consumo_ref * fp_co2, 2),
        "emisiones_acs_kgco2_m2": round(consumo_acs * fp_co2, 2),
        "emisiones_totales_kgco2_m2": round(co2_tot, 2),
        "calificacion_global_emisiones": letra_co2,
        "calificacion_global_consumo": letra_co2
    }
