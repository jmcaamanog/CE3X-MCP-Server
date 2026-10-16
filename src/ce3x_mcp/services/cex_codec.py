import pickle
import io
from typing import Any, List, Dict

class FlexibleCEXObject:
    def __init__(self, cls_name: str):
        self._cls_name = cls_name
    def __setstate__(self, state):
        if isinstance(state, dict):
            self.__dict__.update(state)
        else:
            self.state = state
    def __repr__(self):
        return f"<{self._cls_name}>"

class SafeCEXUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        try:
            return super().find_class(module, name)
        except Exception:
            def make_instance(*args, **kwargs):
                return FlexibleCEXObject(f"{module}.{name}")
            return make_instance

def leer_fichero_cex(ruta_archivo: str) -> List[Any]:
    """
    Lee un archivo nativo .cex de CE3X normalizando los saltos CRLF y resolviendo
    las dependencias de clases compiladas en Python 2.
    """
    with open(ruta_archivo, "rb") as f:
        raw = f.read()
    cleaned = raw.replace(b"\r\n", b"\n")
    stream = io.BytesIO(cleaned)
    unpickler = SafeCEXUnpickler(stream, encoding="latin1")
    
    objetos = []
    while True:
        try:
            obj = unpickler.load()
            objetos.append(obj)
        except EOFError:
            break
        except Exception as e:
            print(f"Aviso al leer objeto en CEX: {e}")
            break
    return objetos

def guardar_fichero_cex_basico(ruta_archivo: str, encabezado: str, admin_data: List[Any], gen_data: List[Any], envolvente_data: List[Any], instalaciones_data: List[Any]):
    """
    Guarda un archivo de proyecto .cex serializado en formato compatible con CE3X.
    """
    with open(ruta_archivo, "wb") as f:
        # En CE3X se usa pickle protocolo 0 con CRLF
        p = pickle.Pickler(f, protocol=0)
        p.dump(encabezado)
        p.dump(admin_data)
        p.dump(gen_data)
        p.dump(envolvente_data)
        p.dump(instalaciones_data)


