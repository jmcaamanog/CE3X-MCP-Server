import requests
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional

CATASTRO_BASE_URL = "http://ovc.catastro.meh.es/ovcservweb/ovcswlocalizacionrc/ovccallejero.asmx"

def consultar_catastro_por_rc(referencia_catastral: str) -> Dict[str, Any]:
    """
    Consulta la Sede Electrónica del Catastro de España a través de la Referencia Catastral (20 caracteres).
    Devuelve los datos del inmueble, dirección oficial, año y superficie si están disponibles.
    """
    rc = referencia_catastral.strip().upper()
    url = f"{CATASTRO_BASE_URL}/Consulta_DNPRC"
    params = {
        "Provincia": "",
        "Municipio": "",
        "RC": rc
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            # Buscar datos de localización
            domicilio = root.find(".//ldt")
            municipio = root.find(".//nm")
            provincia = root.find(".//np")
            cp = root.find(".//dp")
            
            return {
                "valido": True,
                "referencia_catastral": rc,
                "direccion": domicilio.text if domicilio is not None else "No identificada",
                "municipio": municipio.text if municipio is not None else "",
                "provincia": provincia.text if provincia is not None else "",
                "codigo_postal": cp.text if cp is not None else "",
                "fuente": "Sede Electrónica del Catastro (OVC)"
            }
        else:
            return {
                "valido": False,
                "error": f"Respuesta de Catastro con código HTTP {resp.status_code}"
            }
    except Exception as e:
        return {
            "valido": False,
            "error": f"Fallo al conectar con Catastro: {str(e)}"
        }


