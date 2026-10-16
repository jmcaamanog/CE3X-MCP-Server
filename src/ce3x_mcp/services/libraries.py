"""
Módulo de Bibliotecas y Catálogos Constructivos para CE3X
Contiene arquetipos oficiales y normativos del parque edificatorio español
(Pre-1979, NBE-CT-79, CTE DB-HE 2006, 2013, 2019) según IDAE y CE3X.
"""

from typing import Dict, Any, List

CATALOGO_MUROS_FACHADA: Dict[str, Dict[str, Any]] = {
    "MURO_PIEDRA_TRADICIONAL": {
        "nombre": "Muro tradicional de mampostería o sillería de piedra (Galicia/Norte)",
        "periodo": "Pre-1979",
        "espesor_m": 0.60,
        "transmitancia_U": 2.20,
        "masa_kg_m2": 1400.0,
        "descripcion": "Muro portante de granito o esquisto sin aislamiento térmico."
    },
    "MURO_LADRILLO_MACIZO_PRE79": {
        "nombre": "Muro de un pie de ladrillo macizo / perforado sin aislamiento",
        "periodo": "Pre-1979",
        "espesor_m": 0.28,
        "transmitancia_U": 1.85,
        "masa_kg_m2": 320.0,
        "descripcion": "Cerramiento habitual antes de 1980 con cámara de aire no ventilada sin aislar."
    },
    "FACHADA_CAPUCHINA_NBE79": {
        "nombre": "Fachada capuchina tradicional con cámara y aislamiento incipiente (NBE-CT-79)",
        "periodo": "1980-2006",
        "espesor_m": 0.27,
        "transmitancia_U": 0.72,
        "masa_kg_m2": 260.0,
        "descripcion": "Ladrillo caravista exterior + cámara con 2.5-3 cm de fibra o poliuretano + tabique interior."
    },
    "FACHADA_CTE_2006": {
        "nombre": "Fachada aislada conforme a CTE DB-HE 2006",
        "periodo": "2006-2013",
        "espesor_m": 0.30,
        "transmitancia_U": 0.42,
        "masa_kg_m2": 270.0,
        "descripcion": "Cerramiento exterior con 5-6 cm de aislamiento térmico de lana mineral o EPS."
    },
    "FACHADA_CTE_2019_EECN": {
        "nombre": "Fachada de alta eficiencia energética / EECN (CTE DB-HE 2019)",
        "periodo": "2019-Actualidad",
        "espesor_m": 0.34,
        "transmitancia_U": 0.24,
        "masa_kg_m2": 280.0,
        "descripcion": "Fachada con 10-12 cm de aislamiento térmico continuo (tipo SATE o fachada ventilada)."
    }
}

CATALOGO_VIDRIOS: Dict[str, Dict[str, Any]] = {
    "SIMPLE_MONOLITICO_4MM": {
        "nombre": "Vidrio monolítico simple (4 mm)",
        "transmitancia_Ug": 5.70,
        "factor_solar_g": 0.85,
        "periodo_tipico": "Pre-1985",
        "descripcion": "Vidrio plano sencillo sin cámara, muy frecuente en carpinterías antiguas."
    },
    "DOBLE_4_6_4_ESTANDAR": {
        "nombre": "Doble acristalamiento estándar (4/6/4)",
        "transmitancia_Ug": 3.30,
        "factor_solar_g": 0.78,
        "periodo_tipico": "1985-2006",
        "descripcion": "Doble acristalamiento tradicional con cámara pequeña de aire (Climalit básico)."
    },
    "DOBLE_4_12_4_CAMARA_AIRE": {
        "nombre": "Doble acristalamiento con cámara media (4/12/4)",
        "transmitancia_Ug": 2.80,
        "factor_solar_g": 0.76,
        "periodo_tipico": "2006-2015",
        "descripcion": "Doble vidrio con cámara de aire de 12 mm estándar CTE 2006."
    },
    "DOBLE_BAJO_EMISIVO_4_16_4_ARGON": {
        "nombre": "Doble vidrio bajo emisivo con gas argón (4/16/4 Low-E)",
        "transmitancia_Ug": 1.10,
        "factor_solar_g": 0.55,
        "periodo_tipico": "2015-Actualidad",
        "descripcion": "Acristalamiento de altas prestaciones térmicas con tratamiento térmico y gas argón al 90%."
    },
    "TRIPLE_ALTA_EFICIENCIA_4_14_4_14_4": {
        "nombre": "Triple vidrio de alta eficiencia (Passivhaus / EECN)",
        "transmitancia_Ug": 0.60,
        "factor_solar_g": 0.45,
        "periodo_tipico": "Actualidad",
        "descripcion": "Triple acristalamiento para edificios de consumo de energía casi nulo."
    }
}

CATALOGO_MARCOS_CARPINTERIA: Dict[str, Dict[str, Any]] = {
    "METALICO_SIN_RPT": {
        "nombre": "Marco metálico de aluminio sin rotura de puente térmico (marco frío)",
        "transmitancia_Uf": 5.70,
        "absortividad": 0.60,
        "descripcion": "Aluminio lacado o anodizado sin rotura térmica, muy frío en invierno (condensaciones)."
    },
    "METALICO_CON_RPT_MENOR_12": {
        "nombre": "Marco metálico de aluminio con RPT básica (4-12 mm)",
        "transmitancia_Uf": 3.80,
        "absortividad": 0.60,
        "descripcion": "Aluminio con rotura de puente térmico mediante poliamida de 4 a 12 mm."
    },
    "METALICO_CON_RPT_MAYOR_12": {
        "nombre": "Marco metálico de aluminio con RPT avanzada (> 12 mm)",
        "transmitancia_Uf": 2.60,
        "absortividad": 0.60,
        "descripcion": "Carpintería de aluminio de alta gama con poliamida reforzada."
    },
    "PVC_2_3_CAMARAS": {
        "nombre": "Marco de PVC de 2 o 3 cámaras",
        "transmitancia_Uf": 2.20,
        "absortividad": 0.40,
        "descripcion": "Carpintería de PVC estándar de primera generación."
    },
    "PVC_5_CAMARAS_CLASE_A": {
        "nombre": "Marco de PVC de 5 o más cámaras (Clase A)",
        "transmitancia_Uf": 1.30,
        "absortividad": 0.40,
        "descripcion": "Carpintería de PVC moderna de alta eficiencia."
    },
    "MADERA_ESTANDAR": {
        "nombre": "Marco de madera de densidad media (pino/castaño)",
        "transmitancia_Uf": 2.20,
        "absortividad": 0.70,
        "descripcion": "Carpintería de madera tradicional bien ajustada."
    }
}

def inferir_solucion_envolvente_por_ano(ano_construccion: int, region: str = "Norte") -> Dict[str, Any]:
    """
    Deduce automáticamente la solución constructiva más probable de envolvente
    según la fecha de edificación y la región bioclimática.
    """
    if ano_construccion < 1980:
        if "galicia" in region.lower() or "norte" in region.lower() or "coruña" in region.lower():
            muro = CATALOGO_MUROS_FACHADA["MURO_PIEDRA_TRADICIONAL"]
        else:
            muro = CATALOGO_MUROS_FACHADA["MURO_LADRILLO_MACIZO_PRE79"]
        vidrio = CATALOGO_VIDRIOS["SIMPLE_MONOLITICO_4MM"]
        marco = CATALOGO_MARCOS_CARPINTERIA["METALICO_SIN_RPT"]
    elif ano_construccion < 2007:
        muro = CATALOGO_MUROS_FACHADA["FACHADA_CAPUCHINA_NBE79"]
        vidrio = CATALOGO_VIDRIOS["DOBLE_4_6_4_ESTANDAR"]
        marco = CATALOGO_MARCOS_CARPINTERIA["METALICO_SIN_RPT"]
    elif ano_construccion < 2020:
        muro = CATALOGO_MUROS_FACHADA["FACHADA_CTE_2006"]
        vidrio = CATALOGO_VIDRIOS["DOBLE_4_12_4_CAMARA_AIRE"]
        marco = CATALOGO_MARCOS_CARPINTERIA["METALICO_CON_RPT_MENOR_12"]
    else:
        muro = CATALOGO_MUROS_FACHADA["FACHADA_CTE_2019_EECN"]
        vidrio = CATALOGO_VIDRIOS["DOBLE_BAJO_EMISIVO_4_16_4_ARGON"]
        marco = CATALOGO_MARCOS_CARPINTERIA["PVC_5_CAMARAS_CLASE_A"]

    return {
        "ano_construccion": ano_construccion,
        "fachada_recomendada": muro,
        "vidrio_recomendado": vidrio,
        "marco_recomendado": marco
    }
