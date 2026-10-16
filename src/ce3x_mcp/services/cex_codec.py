import pickle
import io
import sys
import types
import os
from importlib.machinery import ModuleSpec
from importlib.abc import Loader
from typing import Any, List, Dict, Optional

CE3X_MODULE_PREFIXES = (
    "BD",
    "Envolvente",
    "Escala",
    "LibreriasCE3X",
    "MedidasDeMejora",
    "PatronesDeSombra",
    "Instalaciones",
    "DefinirSombras",
    "Resultados",
    "datosEdificio",
    "ventanaSubgrupo",
    "models"
)

class AutoModule(types.ModuleType):
    def __getattr__(self, name):
        cls = type(name, (object,), {
            "__module__": self.__name__,
            "__init__": lambda self, *a, **kw: None,
            "__setstate__": lambda self, state: self.__dict__.update(state) if isinstance(state, dict) else setattr(self, "state", state)
        })
        setattr(self, name, cls)
        return cls

class DummyLoader(Loader):
    def create_module(self, spec):
        return AutoModule(spec.name)
    def exec_module(self, module):
        pass

class CE3XFinder:
    def find_spec(self, fullname, path, target=None):
        if any(fullname == p or fullname.startswith(p + ".") for p in CE3X_MODULE_PREFIXES):
            return ModuleSpec(fullname, DummyLoader())
        return None

# Registrar CE3XFinder solo si no está ya registrado
if not any(isinstance(f, CE3XFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, CE3XFinder())

TEMPLATE_CEX_PATH = r"C:\Program Files (x86)\CE3Xv3.2\Ejemplos\2 Vivienda dentro de bloque.cex"

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
    nombre_tecnico: str = "Técnico Certificador Colegiado",
    nif_tecnico: str = "00000000T",
    titulacion: str = "Arquitectura técnica o aparejadores"
):
    """
    Genera un archivo de proyecto .cex 100% compatible con la interfaz gráfica de CE3X v3.2.
    Utiliza la estructura secuencial de 15 objetos que espera el unpickler de wxPython/py2exe.
    """
    if not os.path.exists(TEMPLATE_CEX_PATH):
        raise FileNotFoundError(f"Plantilla base CE3X no encontrada en {TEMPLATE_CEX_PATH}")
        
    with open(TEMPLATE_CEX_PATH, "rb") as f:
        raw = f.read().replace(b"\r\n", b"\n")
        
    unpickler = pickle.Unpickler(io.BytesIO(raw), encoding="latin1")
    items = []
    while True:
        try:
            items.append(unpickler.load())
        except EOFError:
            break

    if len(items) < 15:
        raise ValueError(f"La plantilla cargada tiene {len(items)} objetos, se requieren 15.")

    # 1. Modificar Datos Administrativos (Item 1)
    items[1][0] = str(nombre_edificio)
    items[1][1] = str(direccion)
    items[1][2] = str(municipio)
    items[1][3] = str(provincia)
    items[1][4] = str(codigo_postal)
    items[1][10] = str(nombre_tecnico)
    items[1][11] = str(nif_tecnico)
    items[1][14] = str(municipio)
    items[1][15] = str(provincia)
    items[1][17] = str(titulacion)

    # 2. Modificar Datos Generales (Item 2)
    normativa = "Anterior" if ano_construccion < 1979 else ("NBE-CT-79" if ano_construccion < 2006 else "CTE 2006")
    items[2][0] = normativa
    items[2][2] = str(provincia)
    items[2][3] = str(municipio)
    items[2][4] = str(zona_climatica)
    items[2][6] = f"{float(superficie_util):.2f}"
    items[2][19] = str(ano_construccion)

    # 3. Serializar con pickle protocolo 0 y CRLF
    bio = io.BytesIO()
    p = pickle.Pickler(bio, protocol=0)
    for it in items:
        p.dump(it)
        
    final_bytes = bio.getvalue().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    with open(ruta_salida, "wb") as f:
        f.write(final_bytes)
        
    return ruta_salida

# Alias de compatibilidad
guardar_fichero_cex_basico = guardar_fichero_cex_completo
