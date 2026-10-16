import pymupdf
import re
from typing import Dict, Any, List, Optional

PALABRAS_ESTANCIA = [
    "salón", "salon", "estar", "comedor", "dormitorio", "habitación", "habitacion",
    "cocina", "baño", "bano", "aseo", "pasillo", "distribuidor", "vestíbulo",
    "vestibulo", "terraza", "tendedero", "recibidor", "despacho", "vestidor",
    "galería", "galeria", "lavadero", "trastero", "despensa", "estudio", "ropero",
    "hall", "buhardilla", "balcón", "balcon"
]

def analizar_plano_distribucion_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Abre y analiza un plano de distribución arquitectónico en PDF mediante PyMuPDF.
    Extrae:
    - Textos de estancias (ej. Salón, Dormitorio, Cocina, Baño, Vestidor, Galería) y sus superficies en m².
    - Cuadros de carpinterías y dimensiones de ventanas (ej. 120x120, 150x210).
    - Sumatorio de superficie útil estimada.
    """
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:
        return {"valido": False, "error": f"No se pudo abrir el archivo PDF: {str(e)}"}
        
    estancias_detectadas: List[Dict[str, Any]] = []
    ventanas_detectadas: List[Dict[str, Any]] = []
    textos_completos: List[str] = []
    
    # Expresiones regulares para cazar recintos y superficies
    regex_superficie = re.compile(r'(\d+[.,]\d+)\s*(?:m2|m²|mts2)', re.IGNORECASE)
    regex_ventana = re.compile(r'(?:V|H|P)\s*[-_]?\s*(\d+)\s*[:xX/]\s*(\d+)', re.IGNORECASE)

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        blocks = page.get_text("blocks")  # (x0, y0, x1, y1, text, block_no, block_type)
        
        for b in blocks:
            text = b[4].strip()
            textos_completos.append(text)
            lineas = [l.strip() for l in text.split('\n') if l.strip()]
            
            # 1. Buscar estancias y superficies en el mismo bloque o líneas adyacentes
            for i, linea in enumerate(lineas):
                linea_lower = linea.lower()
                for palabra in PALABRAS_ESTANCIA:
                    if palabra in linea_lower:
                        # Buscar superficie en la misma línea o en la línea inmediatamente siguiente
                        area = 0.0
                        match_sup = regex_superficie.search(linea)
                        if match_sup:
                            try:
                                area = float(match_sup.group(1).replace(',', '.'))
                            except ValueError:
                                pass
                        elif i + 1 < len(lineas):
                            match_next = regex_superficie.search(lineas[i + 1])
                            if match_next:
                                try:
                                    area = float(match_next.group(1).replace(',', '.'))
                                except ValueError:
                                    pass
                        if area <= 0:
                            # Buscar en el texto global del bloque
                            match_block = regex_superficie.search(text)
                            if match_block:
                                try:
                                    area = float(match_block.group(1).replace(',', '.'))
                                except ValueError:
                                    pass

                        estancias_detectadas.append({
                            "nombre": linea,
                            "superficie_m2": area,
                            "pagina": page_idx + 1
                        })
                        break
                        
            # 2. Buscar menciones a ventanas
            match_v = regex_ventana.finditer(text)
            for mv in match_v:
                ancho_cm = float(mv.group(1))
                alto_cm = float(mv.group(2))
                ancho_m = ancho_cm / 100.0 if ancho_cm > 10 else ancho_cm
                alto_m = alto_cm / 100.0 if alto_cm > 10 else alto_cm
                area_m2 = round(ancho_m * alto_m, 2)
                ventanas_detectadas.append({
                    "codigo": mv.group(0),
                    "ancho_m": round(ancho_m, 2),
                    "alto_m": round(alto_m, 2),
                    "area_m2": area_m2,
                    "pagina": page_idx + 1
                })

    # Deduplicar estancias
    estancias_unicas = []
    nombres_vistos = set()
    for est in estancias_detectadas:
        key = (est["nombre"].lower(), est["superficie_m2"])
        if key not in nombres_vistos:
            nombres_vistos.add(key)
            estancias_unicas.append(est)
            
    superficie_util_total = sum(e["superficie_m2"] for e in estancias_unicas if e["superficie_m2"] > 0)
    
    return {
        "valido": True,
        "paginas_analizadas": len(doc),
        "num_estancias_detectadas": len(estancias_unicas),
        "estancias": estancias_unicas,
        "superficie_util_total_detectada_m2": round(superficie_util_total, 2),
        "num_ventanas_detectadas": len(ventanas_detectadas),
        "ventanas": ventanas_detectadas
    }
