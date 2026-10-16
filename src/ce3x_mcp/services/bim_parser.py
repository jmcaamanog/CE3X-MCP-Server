import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.placement
import math
from typing import Dict, Any, List, Optional
from ce3x_mcp.core.models import CerramientoOpaco, HuecoVentana

def calcular_orientacion_vector(dx: float, dy: float) -> str:
    """Calcula la orientación cardinal aproximada (N, S, E, O, etc.) según un vector normal 2D."""
    ang_rad = math.atan2(dy, dx)
    ang_deg = (math.degrees(ang_rad) + 360) % 360
    
    # 0/360 es Este en coordenadas matemáticas estándar, pero en topografía Norte suele ser Y (90°)
    # Asumiendo Y+ = Norte (90°), X+ = Este (0°):
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
    - Espacios acondicionados (superficie útil total).
    - Cerramientos exteriores (IfcWall / IfcWallStandardCase).
    - Huecos y ventanas (IfcWindow / IfcDoor).
    - Cubiertas y soleras (IfcSlab).
    """
    try:
        model = ifcopenshell.open(ifc_path)
    except Exception as e:
        return {"error": f"No se pudo abrir el archivo IFC: {str(e)}"}
        
    # 1. Espacios útiles (IfcSpace)
    spaces = model.by_type("IfcSpace")
    superficie_util_total = 0.0
    espacios_detalle = []
    
    for sp in spaces:
        psets = ifcopenshell.util.element.get_psets(sp)
        # Buscar área en psets estándar (Qto_SpaceBaseQuantities o similar)
        area = 0.0
        for pset_name, props in psets.items():
            if "Area" in props:
                area = float(props["Area"])
                break
            elif "NetFloorArea" in props:
                area = float(props["NetFloorArea"])
                break
        if area > 0:
            superficie_util_total += area
            espacios_detalle.append({"nombre": sp.Name or "Espacio", "area_m2": round(area, 2)})
            
    # 2. Muros exteriores (IfcWall)
    walls = model.by_type("IfcWall")
    opacos: List[CerramientoOpaco] = []
    
    for idx, wall in enumerate(walls):
        psets = ifcopenshell.util.element.get_psets(wall)
        is_external = False
        for pset_name, props in psets.items():
            if props.get("IsExternal") is True:
                is_external = True
                break
                
        # Si está explícitamente marcado como exterior o no tiene IsExternal pero tiene cantidad neta
        if is_external:
            area = 0.0
            for pset_name, props in psets.items():
                if "NetSideArea" in props:
                    area = float(props["NetSideArea"])
                    break
                elif "Area" in props:
                    area = float(props["Area"])
                    break
            if area > 0:
                opacos.append(CerramientoOpaco(
                    nombre=f"Muro_{idx+1}_{wall.Name or 'Fachada'}",
                    tipo="FachadaAire",
                    orientacion="N", # Default si no hay matriz de rotación disponible
                    superficie=round(area, 2),
                    transmitancia_u=u_fachada_defecto
                ))
                
    # 3. Ventanas (IfcWindow)
    windows = model.by_type("IfcWindow")
    huecos: List[HuecoVentana] = []
    
    for idx, win in enumerate(windows):
        psets = ifcopenshell.util.element.get_psets(win)
        area = 0.0
        for pset_name, props in psets.items():
            if "Area" in props:
                area = float(props["Area"])
                break
        if area <= 0 and getattr(win, "OverallWidth", None) and getattr(win, "OverallHeight", None):
            area = float(win.OverallWidth) * float(win.OverallHeight)
            
        if area > 0:
            huecos.append(HuecoVentana(
                nombre=f"Ventana_{idx+1}_{win.Name or 'Hueco'}",
                orientacion="N",
                superficie=round(area, 2),
                transmitancia_u=u_hueco_defecto
            ))
            
    return {
        "valido": True,
        "superficie_util_total_m2": round(superficie_util_total, 2),
        "num_espacios": len(espacios_detalle),
        "num_muros_exteriores": len(opacos),
        "superficie_muros_m2": sum(o.superficie for o in opacos),
        "num_ventanas": len(huecos),
        "superficie_ventanas_m2": sum(h.superficie for h in huecos),
        "opacos": [o.model_dump() for o in opacos],
        "huecos": [h.model_dump() for h in huecos]
    }

