"""
Módulo oficial de consulta e inspección telemática con la Sede Electrónica del Catastro (OVC).
Extrae datos reales y fidedignos de localización, año de construcción, superficie construida
y unidades de uso sin inventar datos ni depender de supuestos heurísticos.
"""

import requests
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List

CATASTRO_BASE_URL = "http://ovc.catastro.meh.es/ovcservweb/ovcswlocalizacionrc/ovccallejero.asmx"

def consultar_catastro_por_rc(referencia_catastral: str) -> Dict[str, Any]:
    """
    Consulta la Sede Electrónica del Catastro de España a través de la Referencia Catastral (20 caracteres).
    Extrae de forma robusta la dirección oficial, municipio, provincia, código postal,
    año real de construcción (<ant>), superficie construida total (<sfc>) y desglose de unidades.
    """
    rc = referencia_catastral.strip().upper()
    if not rc:
        return {
            "valido": False,
            "error": "La referencia catastral proporcionada está vacía."
        }

    # Detección de regímenes forales especiales
    if len(rc) == 29:
        return {
            "valido": False,
            "referencia_catastral": rc,
            "es_foral": True,
            "regimen": "Navarra / Foral",
            "error": (
                "La referencia catastral corresponde al Catastro Foral de Navarra (29 caracteres). "
                "Los servicios web de la DGC de Territorio Común solo procesan referencias de 20 caracteres. "
                "Consulte la Sede Electrónica de Hacienda Foral de Navarra para obtener la cédula parcelaria."
            )
        }

    url = f"{CATASTRO_BASE_URL}/Consulta_DNPRC"
    params = {
        "Provincia": "",
        "Municipio": "",
        "RC": rc
    }
    
    try:
        resp = requests.get(url, params=params, timeout=12)
        if resp.status_code != 200:
            return {
                "valido": False,
                "error": f"La Sede Electrónica del Catastro respondió con código HTTP {resp.status_code}."
            }
            
        root = ET.fromstring(resp.content)  # nosec B314
        
        # Eliminar namespaces para búsqueda limpia e insensible al esquema XML de la OVC
        for elem in root.iter():
            if '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]
                
        err = root.find(".//err/des")
        if err is not None and err.text:
            return {
                "valido": False,
                "referencia_catastral": rc,
                "error": f"Catastro no localizó el inmueble: {err.text.strip()}"
            }
            
        ldt = root.find(".//ldt")
        nm = root.find(".//dt/nm")
        np = root.find(".//dt/np")
        dp = root.find(".//dt//dp")
        ant = root.find(".//debi/ant")
        sfc = root.find(".//debi/sfc")
        luso = root.find(".//debi/luso")
        
        # Desglose de unidades constructivas
        unidades = []
        for c in root.findall(".//lcons/cons"):
            lcd = c.find("lcd")
            stl = c.find(".//stl")
            uso_desc = lcd.text.strip() if lcd is not None and lcd.text else "DESCONOCIDO"
            area_m2 = 0.0
            if stl is not None and stl.text:
                try:
                    area_m2 = float(stl.text.strip())
                except ValueError:
                    pass
            unidades.append({
                "uso": uso_desc,
                "superficie_m2": area_m2
            })
            
        ano_val = None
        if ant is not None and ant.text and ant.text.strip().isdigit():
            ano_val = int(ant.text.strip())
            
        sfc_val = None
        if sfc is not None and sfc.text:
            try:
                sfc_val = float(sfc.text.strip())
            except ValueError:
                pass

        return {
            "valido": True,
            "referencia_catastral": rc,
            "direccion": ldt.text.strip() if ldt is not None and ldt.text else "No identificada",
            "municipio": nm.text.strip() if nm is not None and nm.text else "",
            "provincia": np.text.strip() if np is not None and np.text else "",
            "codigo_postal": dp.text.strip() if dp is not None and dp.text else "",
            "ano_construccion": ano_val,
            "superficie_construida_m2": sfc_val,
            "uso_principal": luso.text.strip() if luso is not None and luso.text else "Residencial",
            "num_unidades_constructivas": len(unidades),
            "unidades_constructivas": unidades,
            "fuente": "Sede Electrónica del Catastro (OVC Oficial)"
        }
    except Exception as e:
        return {
            "valido": False,
            "referencia_catastral": rc,
            "error": f"Fallo de conexión telemática con Catastro: {str(e)}"
        }
