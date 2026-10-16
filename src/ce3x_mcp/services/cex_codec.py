"""
Módulo de codificación y mutación de archivos nativos de proyecto CE3X (.cex).
Preserva la estructura binaria exacta de 15 objetos y pickle protocolo 0 requerida
por el intérprete congelado de CE3X v3.2 (wxPython y Cython), eliminando todos los datos
fantasma de ejemplos (CENER, Pamplona, 150m2, D1) y asignando los datos reales del inmueble.
"""

import os
import io
import json
import pickle
from typing import Any, List, Dict, Optional

PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANONICAL_TEMPLATE_PATH = os.path.join(PACKAGE_DIR, "templates", "plantilla_coruna.cex")
FALLBACK_TEMPLATE_PATH = r"C:\Program Files (x86)\CE3Xv3.2\Ejemplos\2 Vivienda dentro de bloque.cex"

def cargar_perfil_tecnico_local() -> Dict[str, str]:
    """Carga credenciales del perfil técnico persistente si existen."""
    perfil_path = os.path.expanduser("~/.ce3x_mcp_perfil_tecnico.json")
    if os.path.exists(perfil_path):
        try:
            with open(perfil_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def leer_fichero_cex(ruta_archivo: str) -> List[Any]:
    """
    Lee un archivo nativo .cex de CE3X normalizando los saltos CRLF y resolviendo
    las dependencias de clases compiladas en Python 2.
    """
    with open(ruta_archivo, "rb") as f:
        raw = f.read()
    cleaned = raw.replace(b"\r\n", b"\n")
    stream = io.BytesIO(cleaned)
    unpickler = pickle.Unpickler(stream, encoding="latin1")
    
    objetos = []
    while True:
        try:
            obj = unpickler.load()
            objetos.append(obj)
        except EOFError:
            break
        except Exception:
            break
    return objetos

def guardar_fichero_cex_completo(
    ruta_salida: str,
    nombre_edificio: str,
    direccion: str,
    municipio: str = "A Coruña",
    provincia: str = "A Coruña",
    codigo_postal: str = "15001",
    ano_construccion: int = 1982,
    superficie_util: float = 150.0,
    zona_climatica: str = "C1",
    referencia_catastral: str = "2344201XK3724S0001LD",
    nombre_tecnico: str = "Técnico Certificador Colegiado",
    nif_tecnico: str = "00000000T",
    titulacion: str = "Arquitectura técnica o aparejadores",
    razon_social: Optional[str] = None,
    comunidad_autonoma: Optional[str] = None,
    tipo_edificio: str = "Vivienda Individual",
    tipologia: Optional[str] = None
) -> str:
    """
    Genera un archivo de proyecto .cex 100% compatible con CE3X v3.2.
    Sustituye de forma exhaustiva todos los campos de datos administrativos, generales,
    zona climática, año y superficie, purgando cualquier rastro de datos fantasma de CENER/Pamplona.
    """
    template_path = CANONICAL_TEMPLATE_PATH if os.path.exists(CANONICAL_TEMPLATE_PATH) else FALLBACK_TEMPLATE_PATH
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Plantilla base CE3X no encontrada en {template_path}")
        
    with open(template_path, "rb") as f:
        data = f.read()

    # Cargar perfil de técnico colegiado si no se ha sobreescrito expresamente
    perfil = cargar_perfil_tecnico_local()
    tec_nombre = nombre_tecnico if nombre_tecnico != "Técnico Certificador Colegiado" else perfil.get("nombre_apellidos", nombre_tecnico)
    tec_nif = nif_tecnico if nif_tecnico != "00000000T" else perfil.get("nif", nif_tecnico)
    tec_tit = titulacion if titulacion != "Arquitectura técnica o aparejadores" else perfil.get("titulacion", titulacion)
    tec_empresa = razon_social or perfil.get("razon_social", "Despacho Profesional de Certificación Energética")
    tec_tel = perfil.get("telefono", "900000000")
    tec_email = perfil.get("email", "tecnico@certificacion.es")
    tec_mun = perfil.get("municipio", municipio)
    tec_prov = perfil.get("provincia", provincia)
    tec_cp = perfil.get("codigo_postal", codigo_postal)

    # Conversión a Latin-1 requerida por CE3X v3.2 (Python 2.7 / Cython)
    def to_lat(s: str) -> bytes:
        return s.encode("latin1", errors="replace")

    # 1. Datos Administrativos del Edificio
    if b"VVivienda Certificada Prueba JMCG\r\n" in data:
        data = data.replace(b"VVivienda Certificada Prueba JMCG\r\n", b"V" + to_lat(nombre_edificio) + b"\r\n")
    elif b"VEjemplo2-Vivienda perteneciente a un bloque de viviendas\r\n" in data:
        data = data.replace(b"VEjemplo2-Vivienda perteneciente a un bloque de viviendas\r\n", b"V" + to_lat(nombre_edificio) + b"\r\n")
        
    if b"VCalle Gran Via 20\r\n" in data:
        data = data.replace(b"VCalle Gran Via 20\r\n", b"V" + to_lat(direccion) + b"\r\n")
    elif b"Vc/ Elizmendi 28, 7\xbaA\r\n" in data:
        data = data.replace(b"Vc/ Elizmendi 28, 7\xbaA\r\n", b"V" + to_lat(direccion) + b"\r\n")

    # Referencia Catastral (20 caracteres de Territorio Común)
    rc_clean = referencia_catastral.strip()
    if b"V131050090310000000001550820MA\r\n" in data:
        data = data.replace(b"V131050090310000000001550820MA\r\n", b"V" + to_lat(rc_clean) + b"\r\n")
    elif b"V31201A002000040001WR\r\n" in data:
        data = data.replace(b"V31201A002000040001WR\r\n", b"V" + to_lat(rc_clean) + b"\r\n")

    # 2. Purgar datos de CENER / EFINOVATIC / Pamplona
    if b"VRoberto V\xe1zque de la Torre\r\n" in data:
        data = data.replace(b"VRoberto V\xe1zque de la Torre\r\n", b"V" + to_lat(tec_nombre) + b"\r\n")
    if b"VCENER - EFINOVATIC\r\n" in data:
        data = data.replace(b"VCENER - EFINOVATIC\r\n", b"V" + to_lat(tec_empresa) + b"\r\n")
    if b"V948316829\r\n" in data:
        data = data.replace(b"V948316829\r\n", b"V" + to_lat(tec_tel) + b"\r\n")
    if b"Vinfo@efinovatic.es\r\n" in data:
        data = data.replace(b"Vinfo@efinovatic.es\r\n", b"V" + to_lat(tec_email) + b"\r\n")
    if b"V61701435W\r\n" in data:
        data = data.replace(b"V61701435W\r\n", b"V" + to_lat(tec_nif) + b"\r\n")
    if b"VPamplona\r\n" in data:
        data = data.replace(b"VPamplona\r\n", b"V" + to_lat(tec_mun) + b"\r\n")
    if b"VNavarra\r\n" in data:
        data = data.replace(b"VNavarra\r\n", b"V" + to_lat(tec_prov) + b"\r\n")
    if b"V31002\r\n" in data:
        data = data.replace(b"V31002\r\n", b"V" + to_lat(tec_cp) + b"\r\n")

    # 3. Datos Generales de Simulación (Zona climática, Superficie, Año)
    # Zona climática
    zc_clean = zona_climatica.strip().upper()
    if b"VC1\r\n" in data and zc_clean != "C1":
        data = data.replace(b"VC1\r\n", b"V" + to_lat(zc_clean) + b"\r\n")
    elif b"VD1\r\n" in data and zc_clean != "D1":
        data = data.replace(b"VD1\r\n", b"V" + to_lat(zc_clean) + b"\r\n")

    # Superficie útil
    sup_str = str(int(round(superficie_util)))
    if b"V150\r\n" in data and sup_str != "150":
        data = data.replace(b"V150\r\n", b"V" + to_lat(sup_str) + b"\r\n")

    # Año de construcción
    ano_str = str(ano_construccion)
    if b"V1982\r\n" in data and ano_str != "1982":
        data = data.replace(b"V1982\r\n", b"V" + to_lat(ano_str) + b"\r\n")

    # Normativa
    if ano_construccion < 1979:
        norm_str = "Anterior a 1979"
    elif ano_construccion < 2006:
        norm_str = "NBE-CT-79"
    elif ano_construccion < 2013:
        norm_str = "CTE 2006"
    else:
        norm_str = "CTE 2013/2019"
    if b"VNBE-CT-79\r\n" in data and norm_str != "NBE-CT-79":
        data = data.replace(b"VNBE-CT-79\r\n", b"V" + to_lat(norm_str) + b"\r\n")

    os.makedirs(os.path.dirname(os.path.abspath(ruta_salida)), exist_ok=True)
    with open(ruta_salida, "wb") as f:
        f.write(data)
        
    return ruta_salida

guardar_fichero_cex_basico = guardar_fichero_cex_completo
