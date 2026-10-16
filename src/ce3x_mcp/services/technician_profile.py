"""
Módulo de Gestión de Perfil del Técnico Certificador
Permite guardar y cargar los datos colegiales y profesionales del técnico (nombre, NIF,
titulación, colegio oficial, número de colegiado, domicilio, etc.) para que se inyecten de forma
automática y persistente en todos los archivos generados (.cex, XML oficial v3.0 y PDFs).
"""

import os
import json
import re
from typing import Dict, Any, Optional, Tuple, List

PROFILE_PATH = os.path.join(os.path.expanduser("~"), ".ce3x_mcp_perfil_tecnico.json")

DEFAULT_PROFILE = {
    "nombre_tecnico": "Técnico Certificador Colegiado",
    "nif_tecnico": "00000000T",
    "titulacion": "Arquitectura técnica o aparejadores",
    "colegio_profesional": "Colegio Oficial Profesional",
    "numero_colegiado": "",
    "razon_social": "Despacho Profesional de Certificación Energética",
    "domicilio": "Domicilio Profesional",
    "municipio": "A Coruña",
    "provincia": "A Coruña",
    "codigo_postal": "15001",
    "comunidad_autonoma": "Galicia",
    "email": "tecnico@certificador.es",
    "telefono": "981000000",
    "perfil_personalizado": False
}

def obtener_perfil_tecnico() -> Dict[str, Any]:
    """Carga el perfil oficial del técnico configurado o el predeterminado."""
    if os.path.exists(PROFILE_PATH):
        try:
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                res = {**DEFAULT_PROFILE, **data}
                if res.get("nombre_tecnico") not in ["", "Técnico Certificador Colegiado"] and res.get("nif_tecnico") not in ["", "00000000T", "00000000Z"]:
                    res["perfil_personalizado"] = True
                return res
        except Exception:
            pass
    return DEFAULT_PROFILE.copy()

def verificar_perfil_tecnico(perfil: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Verifica si el perfil técnico contiene todos los datos preceptivos para el informe oficial."""
    campos_obligatorios = {
        "nombre_tecnico": "Nombre y apellidos del técnico",
        "nif_tecnico": "NIF/NIE del técnico",
        "titulacion": "Titulación habilitante (Arquitecto, Arquitecto Técnico, etc.)",
        "colegio_profesional": "Colegio oficial profesional",
        "domicilio": "Domicilio profesional",
        "municipio": "Municipio profesional",
        "provincia": "Provincia profesional",
        "codigo_postal": "Código postal profesional",
        "telefono": "Teléfono de contacto",
        "email": "Correo electrónico profesional"
    }
    placeholders = [
        "técnico certificador colegiado", "00000000t", "00000000z", "colegio oficial profesional",
        "colegio oficial correspondiente", "domicilio profesional", "tecnico@certificador.es"
    ]
    faltantes = []
    for campo, desc in campos_obligatorios.items():
        val = str(perfil.get(campo, "")).strip()
        if not val or val.lower() in placeholders:
            faltantes.append(desc)
    return (len(faltantes) == 0, faltantes)

def extraer_perfil_tecnico_de_texto(texto: str) -> Optional[Dict[str, Any]]:
    """
    Extrae automáticamente los datos del técnico certificador a partir de notas de campo (NOTAS_VISITA.txt).
    Reconoce secciones como 'DATOS DEL TÉCNICO', 'TÉCNICO CERTIFICADOR', etc.
    """
    if not texto:
        return None

    patterns = {
        'nombre_tecnico': r'(?:^|[\r\n])\s*[-*•]?\s*(?:nombre\s*(?:y\s*apellidos)?|t[eé]cnico|certificador)\s*[:=]\s*([^\r\n]+)',
        'nif_tecnico': r'(?:^|[\r\n])\s*[-*•]?\s*(?:nif|nie|cif|dni)\s*(?:t[eé]cnico)?\s*[:=]\s*([0-9XYZxyz][0-9]{7}[A-Za-z]|[A-Za-z][0-9]{7}[0-9A-Za-z])',
        'titulacion': r'(?:^|[\r\n])\s*[-*•]?\s*(?:titulaci[oó]n(?:\s*habilitante)?|profesi[oó]n|habilitaci[oó]n)\s*[:=]\s*([^\r\n]+)',
        'colegio_profesional': r'(?:^|[\r\n])\s*[-*•]?\s*(?:colegio\s*(?:oficial|profesional)?)\s*[:=]\s*([^\r\n]+)',
        'numero_colegiado': r'(?:^|[\r\n])\s*[-*•]?\s*(?:n[uú]mero\s*de\s*colegiado|n[ºo]\.?\s*colegiado|colegiado\s*n[ºo]?\.?)\s*[:=]\s*([^\r\n]+)',
        'razon_social': r'(?:^|[\r\n])\s*[-*•]?\s*(?:raz[oó]n\s*social|empresa|despacho)\s*[:=]\s*([^\r\n]+)',
        'domicilio': r'(?:^|[\r\n])\s*[-*•]?\s*(?:domicilio\s*(?:profesional)?|direcci[oó]n\s*profesional)\s*[:=]\s*([^\r\n]+)',
        'municipio': r'(?:^|[\r\n])\s*[-*•]?\s*(?:municipio|localidad|ciudad)\s*(?:profesional|t[eé]cnico)?\s*[:=]\s*([^\r\n]+)',
        'provincia': r'(?:^|[\r\n])\s*[-*•]?\s*(?:provincia)\s*(?:profesional|t[eé]cnico)?\s*[:=]\s*([^\r\n]+)',
        'codigo_postal': r'(?:^|[\r\n])\s*[-*•]?\s*(?:c[oó]digo\s*postal|cp)\s*(?:profesional|t[eé]cnico)?\s*[:=]\s*(\d{5})',
        'telefono': r'(?:^|[\r\n])\s*[-*•]?\s*(?:tel[eé]fono|m[oó]vil|tfno)\s*(?:profesional|t[eé]cnico)?\s*[:=]\s*([+0-9][0-9\s\-]{7,15})',
        'email': r'(?:^|[\r\n])\s*[-*•]?\s*(?:email|correo(?:\s*electr[oó]nico)?|e-mail)\s*(?:profesional|t[eé]cnico)?\s*[:=]\s*([\w\.\-]+@[\w\.\-]+\.\w+)'
    }

    datos = {}
    for k, p in patterns.items():
        m = re.search(p, texto, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            val = val.rstrip(" -,\t;")
            if val:
                datos[k] = val

    if datos.get("nombre_tecnico") or datos.get("nif_tecnico"):
        datos["perfil_personalizado"] = True
        return datos
    return None

def guardar_perfil_tecnico(
    nombre_tecnico: str,
    nif_tecnico: str,
    titulacion: str = "Arquitecto Técnico",
    colegio_profesional: Optional[str] = None,
    numero_colegiado: Optional[str] = None,
    razon_social: Optional[str] = None,
    domicilio: Optional[str] = None,
    municipio: Optional[str] = None,
    provincia: Optional[str] = None,
    codigo_postal: Optional[str] = None,
    telefono: Optional[str] = None,
    email: Optional[str] = None,
    comunidad_autonoma: str = "Galicia",
    **kwargs
) -> Dict[str, Any]:
    """Guarda persistentemente todos los datos colegiales y profesionales del técnico certificador."""
    perfil = {
        "nombre_tecnico": nombre_tecnico,
        "nif_tecnico": nif_tecnico,
        "titulacion": titulacion,
        "colegio_profesional": colegio_profesional or "Colegio Oficial correspondiente",
        "numero_colegiado": numero_colegiado or "",
        "razon_social": razon_social or nombre_tecnico,
        "domicilio": domicilio or "Domicilio Profesional",
        "municipio": municipio or "A Coruña",
        "provincia": provincia or "A Coruña",
        "codigo_postal": codigo_postal or "15001",
        "telefono": telefono or "981000000",
        "email": email or "tecnico@certificador.es",
        "comunidad_autonoma": comunidad_autonoma,
        "perfil_personalizado": True
    }
    try:
        with open(PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump(perfil, f, indent=2, ensure_ascii=False)
        return {
            "valido": True,
            "mensaje": "Perfil de técnico colegiado guardado con éxito. Se aplicará a todos los certificados.",
            "perfil": perfil
        }
    except Exception as e:
        return {
            "valido": False,
            "mensaje": f"Error al guardar perfil: {str(e)}",
            "perfil": perfil
        }
