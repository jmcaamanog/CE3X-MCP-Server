"""
Módulo de Gestión de Perfil del Técnico Certificador
Permite guardar y cargar los datos colegiales y profesionales del técnico (nombre, NIF,
titulación, colegio oficial y número de colegiado) para que se inyecten de forma automática
y persistente en todos los archivos generados (.cex, XML oficial v3.0 y PDFs).
"""

import os
import json
from typing import Dict, Any, Optional

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
                return {**DEFAULT_PROFILE, **data}
        except Exception:
            pass
    return DEFAULT_PROFILE.copy()

def guardar_perfil_tecnico(
    nombre_tecnico: str,
    nif_tecnico: str,
    titulacion: str = "Arquitecto Técnico",
    colegio_profesional: Optional[str] = None,
    numero_colegiado: Optional[str] = None,
    razon_social: Optional[str] = None,
    comunidad_autonoma: str = "Galicia"
) -> Dict[str, Any]:
    """Guarda persistentemente los datos colegiales del técnico certificador."""
    perfil = {
        "nombre_tecnico": nombre_tecnico,
        "nif_tecnico": nif_tecnico,
        "titulacion": titulacion,
        "colegio_profesional": colegio_profesional or "Colegio Oficial correspondiente",
        "numero_colegiado": numero_colegiado or "",
        "razon_social": razon_social or nombre_tecnico,
        "comunidad_autonoma": comunidad_autonoma
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
