"""
Módulo de Caché Persistente Local con SQLite para CE3X-MCP-Server.
Optimiza el rendimiento y previene el bloqueo por tasa de peticiones (rate limiting)
almacenando en disco las respuestas de la Sede Electrónica del Catastro (OVC)
y del simulador solar satelital PVGIS de la Comisión Europea.
"""

import os
import sqlite3
import json
import time
import tempfile
from typing import Optional, Dict, Any

DEFAULT_CACHE_DIR = os.path.expanduser(os.path.join("~", ".ce3x_mcp"))
DEFAULT_DB_PATH = os.path.join(DEFAULT_CACHE_DIR, "cache.db")

def obtener_ruta_db() -> str:
    """Devuelve una ruta accesible y segura para la base de datos SQLite."""
    override = os.environ.get("CE3X_CACHE_DB")
    if override:
        return override
    try:
        os.makedirs(DEFAULT_CACHE_DIR, exist_ok=True)
        return DEFAULT_DB_PATH
    except Exception:
        tmp_dir = os.path.join(tempfile.gettempdir(), "ce3x_mcp")
        os.makedirs(tmp_dir, exist_ok=True)
        return os.path.join(tmp_dir, "cache.db")

def inicializar_bd(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Inicializa la base de datos con modo WAL para alta concurrencia."""
    path = db_path or obtener_ruta_db()
    conn = sqlite3.connect(path, timeout=5.0)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_cache (
            key TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at REAL NOT NULL,
            ttl_seconds REAL NOT NULL
        );
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_category ON api_cache(category);")
    conn.commit()
    return conn

def obtener_de_cache(categoria: str, clave: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Recupera un objeto JSON de la caché si existe y no ha expirado su TTL.
    """
    conn = None
    try:
        conn = inicializar_bd(db_path)
        cur = conn.execute(
            "SELECT data, created_at, ttl_seconds FROM api_cache WHERE key = ? AND category = ?",
            (clave.strip().upper(), categoria.strip().lower())
        )
        row = cur.fetchone()
        if not row:
            return None
        data_json, created_at, ttl_seconds = row
        # Comprobar expiración
        if (time.time() - created_at) > ttl_seconds:
            with conn:
                conn.execute("DELETE FROM api_cache WHERE key = ?", (clave.strip().upper(),))
            return None
        val = json.loads(data_json)
        if isinstance(val, dict):
            val["cache_hit"] = True
            val["cache_antiguedad_horas"] = round((time.time() - created_at) / 3600.0, 2)
        return val
    except Exception:
        return None
    finally:
        if conn:
            conn.close()

def guardar_en_cache(
    categoria: str,
    clave: str,
    datos: Dict[str, Any],
    ttl_segundos: float = 2592000.0, # 30 días por defecto
    db_path: Optional[str] = None
) -> bool:
    """
    Almacena de forma persistente un objeto en la caché con su TTL.
    """
    conn = None
    try:
        conn = inicializar_bd(db_path)
        datos_limpios = dict(datos)
        datos_limpios.pop("cache_hit", None)
        datos_limpios.pop("cache_antiguedad_horas", None)
        
        data_json = json.dumps(datos_limpios, ensure_ascii=False)
        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO api_cache (key, category, data, created_at, ttl_seconds)
                VALUES (?, ?, ?, ?, ?)
            """, (clave.strip().upper(), categoria.strip().lower(), data_json, time.time(), ttl_segundos))
        return True
    except Exception:
        return False
    finally:
        if conn:
            conn.close()

def purgar_cache_expirada(db_path: Optional[str] = None) -> int:
    """Elimina todas las entradas cuyo TTL haya expirado."""
    conn = None
    try:
        conn = inicializar_bd(db_path)
        with conn:
            cur = conn.execute("DELETE FROM api_cache WHERE (? - created_at) > ttl_seconds", (time.time(),))
            return cur.rowcount
    except Exception:
        return 0
    finally:
        if conn:
            conn.close()

def obtener_estadisticas_cache(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Devuelve estadísticas del almacén de caché local."""
    conn = None
    try:
        conn = inicializar_bd(db_path)
        cur = conn.execute("SELECT category, COUNT(*) FROM api_cache GROUP BY category")
        desglose = {cat: count for cat, count in cur.fetchall()}
        total = sum(desglose.values())
        path = db_path or obtener_ruta_db()
        tamano_bytes = os.path.getsize(path) if os.path.exists(path) else 0
        return {
            "ruta_bd": path,
            "total_entradas": total,
            "desglose_por_categoria": desglose,
            "tamano_kb": round(tamano_bytes / 1024.0, 2)
        }
    except Exception as e:
        return {"error": str(e), "total_entradas": 0}
    finally:
        if conn:
            conn.close()

def vaciar_cache_completa(categoria: Optional[str] = None, db_path: Optional[str] = None) -> int:
    """Vacía las entradas de la caché (de una categoría concreta o todas)."""
    conn = None
    try:
        conn = inicializar_bd(db_path)
        with conn:
            if categoria:
                cur = conn.execute("DELETE FROM api_cache WHERE category = ?", (categoria.strip().lower(),))
            else:
                cur = conn.execute("DELETE FROM api_cache")
            return cur.rowcount
    except Exception:
        return 0
    finally:
        if conn:
            conn.close()
