import requests
from typing import Dict, Any, Optional

PVGIS_API_URL = "https://re.jrc.ec.europa.eu/api/v5_2/PVcalc"

def calcular_produccion_solar_pvgis(
    latitud: float,
    longitud: float,
    potencia_pico_kw: float = 3.0,
    inclinacion_grados: float = 35.0,
    azimut_grados: float = 0.0,
    perdidas_sistema_pct: float = 14.0
) -> Dict[str, Any]:
    """
    Consulta la API oficial PVGIS de la Comisión Europea (JRC) para calcular
    la producción anual y mensual de energía solar fotovoltaica con datos satelitales SARAH-2.
    - azimut_grados: 0 para Sur, 90 para Oeste, -90 para Este, 180 para Norte.
    """
    params = {
        "lat": latitud,
        "lon": longitud,
        "peakpower": potencia_pico_kw,
        "loss": perdidas_sistema_pct,
        "mountingplace": "building",
        "angle": inclinacion_grados,
        "aspect": azimut_grados,
        "outputformat": "json"
    }
    try:
        resp = requests.get(PVGIS_API_URL, params=params, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            totals = data.get("outputs", {}).get("totals", {}).get("fixed", {})
            produccion_anual_kwh = totals.get("E_y", 0.0)
            irradiancia_anual_kwh_m2 = totals.get("H(i)_y", 0.0)
            
            # Obtener datos mensuales
            monthly = data.get("outputs", {}).get("monthly", {}).get("fixed", [])
            meses = [
                {"mes": m.get("month"), "kwh_mes": round(m.get("E_m", 0.0), 1)}
                for m in monthly
            ]
            
            return {
                "valido": True,
                "potencia_pico_kw": potencia_pico_kw,
                "produccion_anual_kwh": round(produccion_anual_kwh, 2),
                "irradiancia_anual_kwh_m2": round(irradiancia_anual_kwh_m2, 2),
                "produccion_mensual_desglosada": meses,
                "fuente": "PVGIS (Joint Research Centre - Comisión Europea)"
            }
        else:
            # Fallback en caso de corte o respuesta no 200: estimación analítica según latitud
            horas_sol_equivalentes = 1450.0 if latitud > 40.0 else 1700.0
            prod_est = potencia_pico_kw * horas_sol_equivalentes * (1.0 - perdidas_sistema_pct / 100.0)
            return {
                "valido": True,
                "estimado_fallback": True,
                "potencia_pico_kw": potencia_pico_kw,
                "produccion_anual_kwh": round(prod_est, 2),
                "fuente": "Estimación analítica basada en horas sol equivalentes (CTE DB-HE)"
            }
    except Exception as e:
        # Fallback analítico si no hay conexión a internet
        horas_sol_equivalentes = 1450.0 if latitud > 40.0 else 1700.0
        prod_est = potencia_pico_kw * horas_sol_equivalentes * (1.0 - perdidas_sistema_pct / 100.0)
        return {
            "valido": True,
            "estimado_fallback": True,
            "potencia_pico_kw": potencia_pico_kw,
            "produccion_anual_kwh": round(prod_est, 2),
            "aviso": f"API PVGIS no disponible ({str(e)}), usando estimación analítica CTE"
        }

