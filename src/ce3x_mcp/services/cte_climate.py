from typing import Dict, Tuple

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

