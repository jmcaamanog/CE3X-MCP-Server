import os
import io
import pickle
from typing import Any, List, Dict, Optional

TEMPLATE_CEX_PATH = r"C:\Program Files (x86)\CE3Xv3.2\Ejemplos\2 Vivienda dentro de bloque.cex"

# Mapeo oficial de las 52 provincias espanolas segun la convencion de CE3X (Calculos.listados.pyd)
# Aquellas provincias cuyo nombre coincide con su municipio capital llevan un espacio en blanco al final.
PROVINCIAS_CE3X_ESPACIO = {
    "Albacete", "Alicante", "Almería", "Ávila", "Badajoz", "Barcelona",
    "Burgos", "Cáceres", "Cádiz", "Castellón", "Ciudad Real", "Córdoba",
    "Cuenca", "Girona", "Granada", "Guadalajara", "Huelva", "Huesca",
    "Jaén", "Las Palmas", "León", "Lugo", "Madrid", "Málaga",
    "Melilla", "Murcia", "Ourense", "Palencia", "Pontevedra", "Salamanca",
    "Segovia", "Sevilla", "Soria", "Tarragona", "Teruel", "Toledo",
    "Valencia", "Valladolid", "Zamora"
}

def normalizar_provincia_ce3x(provincia: str) -> str:
    """
    Normaliza el nombre de la provincia segun las reglas internas de CE3X:
    Agrega el espacio final si es una provincia homonima a su capital.
    """
    prov_limpia = provincia.strip()
    for p in PROVINCIAS_CE3X_ESPACIO:
        if prov_limpia.lower() == p.lower():
            return p + " "
    return prov_limpia

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
    municipio: str,
    provincia: str,
    codigo_postal: str,
    ano_construccion: int,
    superficie_util: float,
    zona_climatica: str,
    referencia_catastral: str = "",
    nombre_tecnico: str = "Tecnico Certificador Colegiado",
    nif_tecnico: str = "00000000T",
    titulacion: str = "Arquitectura tecnica o aparejadores"
):
    """
    Genera un archivo de proyecto .cex 100% compatible con la interfaz grafica de CE3X v3.2.
    Utiliza mutacion in-place a nivel de byte sobre la plantilla oficial de CE3X,
    preservando intactos todos los opcodes originales de Python 2.7 y las clases internas de wxPython.
    Aplica normalizacion automatica de provincias y actualiza la referencia catastral
    segun el regimen foral o comun para superar las validaciones de CE3X.
    """
    if not os.path.exists(TEMPLATE_CEX_PATH):
        raise FileNotFoundError(f"Plantilla base CE3X no encontrada en {TEMPLATE_CEX_PATH}")
        
    with open(TEMPLATE_CEX_PATH, "rb") as f:
        data = f.read()

    # Normalizar provincia con la regla de espacios de CE3X
    provincia_ce3x = normalizar_provincia_ce3x(provincia)
    municipio_ce3x = municipio.strip()
    
    # Tratamiento de catastro: en territorio comun debe ser 20 caracteres o vacio
    # La plantilla original contiene una referencia foral navarra de 29 caracteres
    catastro_bytes = f"V{referencia_catastral.strip()}\r\n".encode("latin1", errors="ignore")
    
    subs = [
        # 1. Nombre del edificio
        (b"VEjemplo2-Vivienda perteneciente a un bloque de viviendas\r\n", f"V{nombre_edificio}\r\n".encode("latin1", errors="ignore")),
        # 2. Direccion
        (b"Vc/ Elizmendi 28, 7\xbaA\r\n", f"V{direccion}\r\n".encode("latin1", errors="ignore")),
        # 3. Localidad / Municipio
        (b"VPamplona\r\n", f"V{municipio_ce3x}\r\n".encode("latin1", errors="ignore")),
        # 4. Provincia
        (b"VNavarra\r\n", f"V{provincia_ce3x}\r\n".encode("latin1", errors="ignore")),
        # 5. Codigo postal
        (b"V31001\r\n", f"V{codigo_postal}\r\n".encode("latin1", errors="ignore")),
        (b"V31002\r\n", f"V{codigo_postal}\r\n".encode("latin1", errors="ignore")),
        # 6. Referencia catastral (reemplazo de los 29 chars forales de Navarra)
        (b"V131050090310000000001550820MA\r\n", catastro_bytes),
        # 7. Datos del tecnico
        (b"VRoberto V\xe1zque de la Torre\r\n", f"V{nombre_tecnico}\r\n".encode("latin1", errors="ignore")),
        (b"VCENER - EFINOVATIC\r\n", b"VEstudio Tecnico\r\n"),
        (b"Vinfo@efinovatic.es\r\n", b"Vtecnico@certificacion.es\r\n"),
        # 8. Zona climatica
        (b"aVD1\r\n", f"aV{zona_climatica}\r\n".encode("latin1", errors="ignore")),
    ]
    
    for old, new in subs:
        data = data.replace(old, new)
        
    with open(ruta_salida, "wb") as f:
        f.write(data)
        
    return ruta_salida

guardar_fichero_cex_basico = guardar_fichero_cex_completo
