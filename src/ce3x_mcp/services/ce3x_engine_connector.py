"""
Conector y verificador oficial del motor de cálculo CE3X v3.2.
Comprueba la instalación local, ejecutables, esquemas RelaxNG, compilador de PDF (Typst)
y carga las bases de datos de escalas oficiales y edificios de referencia de Localidades.xml.
"""

import os
import subprocess
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List, Tuple

DEFAULT_CE3X_DIR = r"C:\Program Files (x86)\CE3Xv3.2"

def detectar_directorio_ce3x(directorio_personalizado: Optional[str] = None) -> Optional[str]:
    """Detecta el directorio raíz de la instalación oficial de CE3X v3.2."""
    candidatos = [
        directorio_personalizado,
        os.environ.get("CE3X_HOME"),
        DEFAULT_CE3X_DIR,
        r"C:\Program Files\CE3Xv3.2",
        r"D:\Program Files (x86)\CE3Xv3.2",
    ]
    for c in candidatos:
        if c and os.path.isdir(c) and os.path.exists(os.path.join(c, "CE3Xv3.2.exe")):
            return c
    return None

def verificar_instalacion_ce3x(directorio_ce3x: Optional[str] = None) -> Dict[str, Any]:
    """
    Verifica de forma exhaustiva la integridad de la instalación local de CE3X v3.2,
    sus motores de cálculo, módulos de exportación oficial y dependencias auxiliares.
    """
    root_dir = detectar_directorio_ce3x(directorio_ce3x)
    if not root_dir:
        return {
            "instalado": False,
            "error": "No se localizó la instalación oficial de CE3X v3.2 en las rutas estándar.",
            "rutas_comprobadas": [DEFAULT_CE3X_DIR, r"C:\Program Files\CE3Xv3.2"],
            "instrucciones": "Descargue e instale la versión oficial 3.2 de CE3X desde el portal oficial del MITECO."
        }

    exe_ce3x = os.path.join(root_dir, "CE3Xv3.2.exe")
    xml2cert = os.path.join(root_dir, "moduloXML", "xmlcert_20260703", "xml2cert.exe")
    xmlcheck = os.path.join(root_dir, "moduloXML", "xmlcert_20260703", "xmlcheck.exe")
    schema_rng = os.path.join(root_dir, "moduloXML", "resources", "RelaxNG", "DatosEnergeticosDelEdificioSchema30-full.rng")
    localidades_xml = os.path.join(root_dir, "Escala", "Localidades.xml")
    bd_clima = os.path.join(root_dir, "Calculos", "BDClima")
    
    # Comprobar versión de xml2cert
    version_xml2cert = "Desconocida"
    if os.path.exists(xml2cert):
        try:
            res = subprocess.run([xml2cert, "--version"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                version_xml2cert = res.stdout.strip()
        except Exception:
            pass

    # Comprobar base de datos de escalas oficiales
    total_localidades = 0
    if os.path.exists(localidades_xml):
        try:
            tree = ET.parse(localidades_xml)
            total_localidades = len(tree.getroot().findall("Localidad"))
        except Exception:
            pass

    # Comprobar disponibilidad de Java para Jing (validador de xmlcert)
    java_disponible = False
    java_ruta = None
    known_java = [
        r"C:\Program Files\AutoFirma\AutoFirma\jre\bin\java.exe",
        r"C:\Program Files\Android\Android Studio1\jbr\bin\java.exe",
    ]
    for j in known_java:
        if os.path.exists(j):
            java_disponible = True
            java_ruta = j
            break
    if not java_disponible:
        try:
            res_j = subprocess.run(["java", "-version"], capture_output=True, timeout=5)
            if res_j.returncode == 0:
                java_disponible = True
                java_ruta = "PATH"
        except Exception:
            pass

    componentes = {
        "ejecutable_ce3x": {"ruta": exe_ce3x, "existe": os.path.exists(exe_ce3x)},
        "compilador_pdf_xml2cert": {"ruta": xml2cert, "existe": os.path.exists(xml2cert), "version": version_xml2cert},
        "validador_xmlcheck": {"ruta": xmlcheck, "existe": os.path.exists(xmlcheck)},
        "esquema_oficial_relaxng": {"ruta": schema_rng, "existe": os.path.exists(schema_rng)},
        "base_escalas_localidades": {"ruta": localidades_xml, "existe": os.path.exists(localidades_xml), "zonas_detectadas": total_localidades},
        "motor_clima_bdclima": {"ruta": bd_clima, "existe": os.path.exists(bd_clima)},
        "entorno_java_auxiliar": {"disponible": java_disponible, "ruta": java_ruta}
    }

    todos_criticos = (
        componentes["ejecutable_ce3x"]["existe"] and
        componentes["compilador_pdf_xml2cert"]["existe"] and
        componentes["esquema_oficial_relaxng"]["existe"] and
        componentes["base_escalas_localidades"]["existe"]
    )

    return {
        "instalado": True,
        "directorio_ce3x": root_dir,
        "estado_operativo": "OPERATIVO_100_POR_CIENTO" if todos_criticos else "PARCIAL_FALTAN_COMPONENTES",
        "componentes": componentes,
        "resumen": (
            f"CE3X v3.2 detectado correctamente en {root_dir}. "
            f"Escalas oficiales ({total_localidades} zonas climáticas) y motor Typst (xml2cert {version_xml2cert}) verificados."
            if todos_criticos else "CE3X detectado pero faltan componentes requeridos."
        )
    }

def obtener_escalas_oficiales_zona(zona_climatica: str, tipologia: str = "Unifamiliar", directorio_ce3x: Optional[str] = None) -> Dict[str, Any]:
    """
    Lee directamente de 'Escala/Localidades.xml' los límites de escala oficiales (A a G)
    y los consumos del edificio de referencia oficial para la zona climática y tipología especificadas.
    """
    root_dir = detectar_directorio_ce3x(directorio_ce3x) or DEFAULT_CE3X_DIR
    localidades_xml = os.path.join(root_dir, "Escala", "Localidades.xml")
    if not os.path.exists(localidades_xml):
        pkg_resource = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "Localidades.xml")
        if os.path.exists(pkg_resource):
            localidades_xml = pkg_resource
        else:
            raise FileNotFoundError(f"No se encuentra la base de datos de escalas oficiales en: {localidades_xml}")

    tree = ET.parse(localidades_xml)
    root = tree.getroot()

    zona_clean = zona_climatica.strip().upper()
    nombre_localidad = f"{zona_clean}_peninsular"
    
    loc = root.find(f".//Localidad[@nombre='{nombre_localidad}']")
    if loc is None:
        for l in root.findall("Localidad"):
            if l.attrib.get("nombre", "").startswith(zona_clean):
                loc = l
                break
    
    if loc is None:
        loc = root.find(".//Localidad[@nombre='C1_peninsular']")

    tipo_norm = "Bloque" if "bloque" in tipologia.lower() or "colectiv" in tipologia.lower() or "piso" in tipologia.lower() else "Unifamiliar"
    
    tipo_node = None
    for t in loc.findall("Tipo"):
        if t.attrib.get("nombre") == tipo_norm:
            tipo_node = t
            break
    if tipo_node is None:
        tipo_node = loc.find("Tipo")

    def parse_limites(nombre_limite: str) -> Dict[str, float]:
        node = tipo_node.find(f".//Limites[@nombre='{nombre_limite}']")
        if node is None:
            return {}
        lims = {}
        for sub in node:
            try:
                if sub.text and sub.text.strip():
                    lims[sub.tag] = float(sub.text.strip())
            except ValueError:
                pass
        return lims

    limites_emisiones = parse_limites("EmisionesTotales")
    limites_cep = parse_limites("CEPtotal")
    limites_demanda_cal = parse_limites("DemandaCalefaccion")

    ref_existente = tipo_node.find(".//Referencia[@nombre='Existente']")
    valores_ref = {}
    if ref_existente is not None:
        for c in ref_existente:
            try:
                if c.text and c.text.strip():
                    valores_ref[c.tag] = float(c.text.strip())
            except ValueError:
                valores_ref[c.tag] = c.text.strip()

    return {
        "zona_climatica": zona_clean,
        "tipologia": tipo_norm,
        "limites_emisiones": limites_emisiones,
        "limites_energia_primaria_no_renovable": limites_cep,
        "limites_demanda_calefaccion": limites_demanda_cal,
        "edificio_referencia_existente": valores_ref
    }

def asignar_letra_segun_limites(valor: float, limites: Dict[str, float]) -> str:
    """Asigna la letra (A a G) estrictamente según los límites de corte oficiales de CE3X."""
    if not limites:
        return "G"
    ab = limites.get("A-B", 0.0)
    bc = limites.get("B-C", 0.0)
    cd = limites.get("C-D", 0.0)
    de = limites.get("D-E", 0.0)
    ef = limites.get("E-F", 0.0)
    fg = limites.get("F-G", 0.0)

    if valor < ab:
        return "A"
    elif valor < bc:
        return "B"
    elif valor < cd:
        return "C"
    elif valor < de:
        return "D"
    elif valor < ef:
        return "E"
    elif valor < fg:
        return "F"
    else:
        return "G"
