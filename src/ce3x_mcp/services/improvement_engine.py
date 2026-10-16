from typing import List, Dict, Any
from ce3x_mcp.core.models import MedidaMejora, ProyectoCertificacion, ResultadoCalificacion

def calcular_paquetes_medidas_mejora(proyecto: ProyectoCertificacion, actual: ResultadoCalificacion) -> List[MedidaMejora]:
    """
    Genera automáticamente los paquetes oficiales de medidas de mejora exigidos por el RD 390/2021:
    1. Medida Envolvente: SATE en fachadas + Ventanas PVC con doble vidrio bajo emisivo.
    2. Medida Instalaciones: Sustitución por Aerotermia de alta eficiencia.
    3. Medida Combinada + Renovables: SATE + Aerotermia + Instalación Solar Fotovoltaica.
    """
    sup = proyecto.generales.superficie_util
    ep_actual = actual.consumo_energia_primaria_nr
    co2_actual = actual.emisiones_co2
    
    # 1. Medida Envolvente (SATE + Ventanas)
    ahorro_env_pct = 38.0
    ep_env = ep_actual * (1.0 - ahorro_env_pct / 100.0)
    co2_env = co2_actual * (1.0 - ahorro_env_pct / 100.0)
    coste_env = sup * 95.0 # aprox 95 €/m² útil
    ahorro_anual_env_eur = (ep_actual - ep_env) * sup * 0.16 # coste medio energía 0.16 €/kWh
    payback_env = coste_env / ahorro_anual_env_eur if ahorro_anual_env_eur > 0 else 15.0
    
    m1 = MedidaMejora(
        nombre="Mejora de Envolvente Térmica (SATE 8cm + Carpinterías PVC Bajo Emisivo)",
        tipo="Envolvente",
        descripcion="Instalación de Sistema de Aislamiento Térmico por el Exterior (SATE) de 8 cm de EPS grafito (U=0.32 W/m²K) y sustitución de carpinterías por ventanas de PVC de 5 cámaras con doble acristalamiento bajo emisivo 4/16/4 con gas argón (U=1.30 W/m²K).",
        inversion_estimada_eur=round(coste_env, 2),
        ahorro_energia_primaria_pct=ahorro_env_pct,
        ahorro_emisiones_pct=ahorro_env_pct,
        ahorro_factura_anual_eur=round(ahorro_anual_env_eur, 2),
        nueva_letra_emisiones="C" if actual.letra_global_emisiones in ["E", "F", "G"] else "B",
        nueva_letra_energia_primaria="C" if actual.letra_global_energia_primaria in ["E", "F", "G"] else "B",
        periodo_retorno_anos=round(payback_env, 1)
    )
    
    # 2. Medida Instalaciones (Aerotermia)
    ahorro_inst_pct = 52.0
    ep_inst = ep_actual * (1.0 - ahorro_inst_pct / 100.0)
    co2_inst = co2_actual * (1.0 - ahorro_inst_pct / 100.0)
    coste_inst = 7500.0 if sup < 120 else 9800.0 # coste tipo equipo aerotermia residencial
    ahorro_anual_inst_eur = (ep_actual - ep_inst) * sup * 0.16
    payback_inst = coste_inst / ahorro_anual_inst_eur if ahorro_anual_inst_eur > 0 else 8.0
    
    m2 = MedidaMejora(
        nombre="Sustitución de Generación Térmica por Bomba de Calor Aerotérmica",
        tipo="Instalaciones",
        descripcion="Sustitución de los equipos térmicos existentes por una bomba de calor aerotérmica de alta eficiencia para producción combinada de calefacción y ACS con SCOP estacional superior a 3.60.",
        inversion_estimada_eur=round(coste_inst, 2),
        ahorro_energia_primaria_pct=ahorro_inst_pct,
        ahorro_emisiones_pct=ahorro_inst_pct,
        ahorro_factura_anual_eur=round(ahorro_anual_inst_eur, 2),
        nueva_letra_emisiones="B",
        nueva_letra_energia_primaria="B",
        periodo_retorno_anos=round(payback_inst, 1)
    )
    
    # 3. Medida Combinada + Fotovoltaica
    ahorro_comb_pct = 76.0
    ep_comb = ep_actual * (1.0 - ahorro_comb_pct / 100.0)
    co2_comb = co2_actual * (1.0 - ahorro_comb_pct / 100.0)
    coste_comb = coste_env + coste_inst + 4500.0 # incluye solar FV 3 kWp
    ahorro_anual_comb_eur = (ep_actual - ep_comb) * sup * 0.16
    payback_comb = coste_comb / ahorro_anual_comb_eur if ahorro_anual_comb_eur > 0 else 10.0
    
    m3 = MedidaMejora(
        nombre="Rehabilitación Integral: SATE + Aerotermia + Solar Fotovoltaica (3 kWp)",
        tipo="Conjunto",
        descripcion="Actuación integral combinando la reducción de la demanda mediante aislamiento SATE y carpinterías eficientes, electrificación de la climatización con aerotermia y generación renovable in situ mediante 3 kWp de paneles solares fotovoltaicos en autoconsumo.",
        inversion_estimada_eur=round(coste_comb, 2),
        ahorro_energia_primaria_pct=ahorro_comb_pct,
        ahorro_emisiones_pct=ahorro_comb_pct,
        ahorro_factura_anual_eur=round(ahorro_anual_comb_eur, 2),
        nueva_letra_emisiones="A",
        nueva_letra_energia_primaria="A",
        periodo_retorno_anos=round(payback_comb, 1)
    )
    
    return [m1, m2, m3]

