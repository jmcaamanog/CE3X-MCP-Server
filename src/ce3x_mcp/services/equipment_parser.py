import re
from typing import Dict, Any, List
from ce3x_mcp.core.models import InstalacionTermica

def analizar_datos_equipo_climatizacion(texto_o_ficha: str) -> Dict[str, Any]:
    """
    Analiza el texto de una ficha técnica o descripción de equipo térmico
    (bomba de calor, aerotermia, caldera, termo) y extrae sus propiedades para CE3X.
    """
    texto = texto_o_ficha.lower()
    
    # 1. Detección de Tecnología y Servicio
    if "aerotermia" in texto or "bomba de calor" in texto or "heat pump" in texto or "vrf" in texto or "inverter" in texto:
        tecnologia = "BombaCalorAerotermia"
        vector = "Electricidad"
        servicio = "Mixto2" if ("acs" in texto and ("calefacción" in texto or "calefaccion" in texto)) else ("ACS" if "acs" in texto else "Calefaccion")
        rendimiento_def = 3.4
    elif "condensación" in texto or "condensacion" in texto:
        tecnologia = "CalderaCondensacion"
        vector = "GasNatural"
        servicio = "Mixto2" if ("acs" in texto or "mixta" in texto) else "Calefaccion"
        rendimiento_def = 0.94
    elif "gasóleo" in texto or "gasoleo" in texto or "gasoil" in texto:
        tecnologia = "CalderaEstandar"
        vector = "Gasoleo"
        servicio = "Mixto2" if ("acs" in texto or "mixta" in texto) else "Calefaccion"
        rendimiento_def = 0.80
    elif "pellet" in texto or "biomasa" in texto:
        tecnologia = "Biomasa"
        vector = "BiomasaPellet"
        servicio = "Calefaccion"
        rendimiento_def = 0.88
    elif "termo" in texto or "eléctrico" in texto or "electrico" in texto or "joule" in texto:
        tecnologia = "EfectoJoule"
        vector = "Electricidad"
        servicio = "ACS" if "termo" in texto else "Calefaccion"
        rendimiento_def = 1.0
    else:
        tecnologia = "CalderaEstandar"
        vector = "GasNatural"
        servicio = "Calefaccion"
        rendimiento_def = 0.82
        
    # 2. Extracción de Potencia (kW) mediante regex
    potencia_kw = 8.0 # valor por defecto prudente
    match_kw = re.search(r'(\d+[.,]?\d*)\s*(?:kw|kilovatios)', texto)
    if match_kw:
        try:
            potencia_kw = float(match_kw.group(1).replace(',', '.'))
        except ValueError:
            pass
    else:
        match_w = re.search(r'(\d+)\s*(?:w|vatios)(?:\b|\s|$)', texto)
        if match_w:
            try:
                potencia_kw = round(float(match_w.group(1)) / 1000.0, 2)
            except ValueError:
                pass
            
    # 3. Extracción de Rendimiento Estacional (SCOP / COP / Rendimiento %)
    rendimiento = rendimiento_def
    match_scop = re.search(r'(?:scop|cop|seer|eer|rendimiento)\s*(?:de\s+|estacional\s+del\s+|[:=]\s*)?(\d+[.,]?\d*)%?', texto)
    if match_scop:
        try:
            val = float(match_scop.group(1).replace(',', '.'))
            if val > 10.0:
                rendimiento = round(val / 100.0, 2)
            elif val > 0:
                rendimiento = val
        except ValueError:
            pass
            
    inst = InstalacionTermica(
        nombre=f"{tecnologia} ({servicio})",
        tipo_servicio=servicio,
        tecnologia=tecnologia,
        vector_energetico=vector,
        rendimiento_estacional=rendimiento,
        potencia_nominal_kw=potencia_kw,
        cobertura_pct=100.0
    )
    
    return {
        "valido": True,
        "servicio_detectado": servicio,
        "tecnologia_detectada": tecnologia,
        "vector_energetico": vector,
        "potencia_nominal_kw": potencia_kw,
        "rendimiento_estacional": rendimiento,
        "objeto_instalacion": inst.model_dump()
    }
