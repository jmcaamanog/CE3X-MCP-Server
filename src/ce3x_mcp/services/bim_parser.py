"""
Módulo de parsing y extracción de envolvente térmica desde modelos BIM IFC (IFC2X3 e IFC4).
Utiliza IfcOpenShell con importación perezosa (lazy import) y extracción robusta compatible con
exportaciones de Autodesk Revit, ArchiCAD y CYPE (español e inglés).
"""

import math
from typing import Dict, Any, List, Optional
from ce3x_mcp.core.models import CerramientoOpaco, HuecoVentana

def calcular_orientacion_vector(dx: float, dy: float) -> str:
    """Calcula la orientación cardinal aproximada (N, S, E, O, etc.) según un vector normal 2D."""
    ang_rad = math.atan2(dy, dx)
    ang_deg = (math.degrees(ang_rad) + 360) % 360
    
    if 67.5 <= ang_deg < 112.5:
        return "N"
    elif 112.5 <= ang_deg < 157.5:
        return "NO"
    elif 157.5 <= ang_deg < 202.5:
        return "O"
    elif 202.5 <= ang_deg < 247.5:
        return "SO"
    elif 247.5 <= ang_deg < 292.5:
        return "S"
    elif 292.5 <= ang_deg < 337.5:
        return "SE"
    elif ang_deg >= 337.5 or ang_deg < 22.5:
        return "E"
    else:
        return "NE"

def extraer_envolvente_desde_ifc(ifc_path: str, u_fachada_defecto: float = 0.45, u_hueco_defecto: float = 2.2) -> Dict[str, Any]:
    """
    Abre un modelo BIM IFC (IFC2X3 o IFC4) mediante IfcOpenShell y extrae:
    - Espacios útiles acondicionados (superficie útil total y detalle por estancia).
    - Cerramientos exteriores (IfcWall / IfcWallStandardCase).
    - Huecos y ventanas (IfcWindow / IfcDoor).
    - Superficies de envolvente térmica para CE3X.
    """
    try:
        import ifcopenshell
        import ifcopenshell.util.element
    except ImportError:
        return {
            "valido": False,
            "error": (
                "El módulo 'ifcopenshell' no está instalado en este entorno de Python. "
                "Para analizar modelos BIM IFC, instálelo ejecutando: pip install ifcopenshell "
                "o instale el extra bim: pip install 'ce3x-mcp-server[bim]'"
            )
        }

    try:
        model = ifcopenshell.open(ifc_path)
    except Exception as e:
        return {"valido": False, "error": f"No se pudo abrir el archivo IFC: {str(e)}"}

    # 1. Espacios útiles (IfcSpace)
    spaces = model.by_type("IfcSpace")
    superficie_util_total = 0.0
    espacios_detalle: List[Dict[str, Any]] = []

    for sp in spaces:
        psets = ifcopenshell.util.element.get_psets(sp)
        
        # Nombre de la estancia
        nombre = sp.LongName or sp.Name or "Espacio"
        if "Datos de identidad" in psets and "Nombre" in psets["Datos de identidad"]:
            nombre = str(psets["Datos de identidad"]["Nombre"])
        elif "Pset_SpaceCommon" in psets and "Reference" in psets["Pset_SpaceCommon"]:
            nombre = str(psets["Pset_SpaceCommon"]["Reference"])

        # Superficie de la estancia (compatible con inglés y español)
        area = 0.0
        for pset_name, props in psets.items():
            for k, v in props.items():
                k_clean = k.lower().replace("á", "a").replace("é", "e")
                if k_clean in ["netfloorarea", "grossfloorarea", "area", "gsa space areas"] and isinstance(v, (int, float)):
                    area = float(v)
                    break
            if area > 0:
                break

        if area > 0:
            superficie_util_total += area
            espacios_detalle.append({"nombre": nombre, "area_m2": round(area, 2)})

    # 2. Muros exteriores (IfcWall / IfcWallStandardCase)
    all_walls = model.by_type("IfcWall") + model.by_type("IfcWallStandardCase")
    seen_wall_ids = set()
    opacos: List[CerramientoOpaco] = []
    
    for idx, wall in enumerate(all_walls):
        if wall.id() in seen_wall_ids:
            continue
        seen_wall_ids.add(wall.id())
        psets = ifcopenshell.util.element.get_psets(wall)

        # Determinar si el cerramiento es exterior
        is_external = False
        if psets.get("Pset_WallCommon", {}).get("IsExternal") is True:
            is_external = True
        elif psets.get("Construcción", {}).get("Función") == "Exterior":
            is_external = True
        elif "fachada" in (wall.Name or "").lower() or "exterior" in (wall.Name or "").lower():
            is_external = True
        else:
            for pset_name, props in psets.items():
                for k, v in props.items():
                    if isinstance(v, str) and ("fachada" in v.lower() or "exterior" in v.lower()):
                        is_external = True
                        break

        if is_external:
            area = 0.0
            for pset_name, props in psets.items():
                for k, v in props.items():
                    k_clean = k.lower().replace("á", "a").replace("é", "e")
                    if k_clean in ["netsidearea", "grosssidearea", "area"] and isinstance(v, (int, float)):
                        area = float(v)
                        break
                if area > 0:
                    break

            if area <= 0:
                cotas = psets.get("Cotas", {})
                lon = cotas.get("Longitud", 0.0)
                alt = cotas.get("Altura", 0.0) or cotas.get("Altura desconectada", 0.0)
                if lon > 0 and alt > 0:
                    area = lon * alt

            if area > 0:
                u_val = u_fachada_defecto
                t_trans = psets.get("Pset_WallCommon", {}).get("ThermalTransmittance")
                if isinstance(t_trans, (int, float)) and t_trans > 0:
                    u_val = float(t_trans)

                opacos.append(CerramientoOpaco(
                    nombre=f"Muro_{idx+1}_{wall.Name or 'Fachada'}",
                    tipo="FachadaAire",
                    orientacion="N",
                    superficie=round(area, 2),
                    transmitancia_u=round(u_val, 2)
                ))

    # 3. Ventanas (IfcWindow)
    windows = model.by_type("IfcWindow")
    huecos: List[HuecoVentana] = []

    for idx, win in enumerate(windows):
        w_w = getattr(win, "OverallWidth", None)
        w_h = getattr(win, "OverallHeight", None)
        area = 0.0
        if w_w and w_h:
            area = float(w_w) * float(w_h)
        else:
            psets = ifcopenshell.util.element.get_psets(win)
            for pset_name, props in psets.items():
                for k, v in props.items():
                    k_clean = k.lower().replace("á", "a")
                    if k_clean in ["area"] and isinstance(v, (int, float)):
                        area = float(v)
                        break
                if area > 0:
                    break

        if area > 0:
            huecos.append(HuecoVentana(
                nombre=f"Ventana_{idx+1}_{win.Name or 'Hueco'}",
                orientacion="N",
                superficie=round(area, 2),
                transmitancia_u=u_hueco_defecto
            ))

    return {
        "valido": True,
        "schema_ifc": model.schema,
        "superficie_util_total_m2": round(superficie_util_total, 2),
        "num_estancias_detectadas": len(espacios_detalle),
        "estancias": espacios_detalle,
        "num_muros_detectados": len(opacos),
        "superficie_envolvente_m2": round(sum(o.superficie for o in opacos), 2),
        "muros_exteriores": [o.model_dump() for o in opacos],
        "num_ventanas_detectadas": len(huecos),
        "superficie_huecos_m2": round(sum(h.superficie for h in huecos), 2),
        "ventanas": [h.model_dump() for h in huecos]
    }
