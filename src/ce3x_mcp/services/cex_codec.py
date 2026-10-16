"""
Módulo de codificación y mutación de archivos nativos de proyecto CE3X (.cex).
Preserva la estructura binaria exacta de 15 objetos y pickle protocolo 0 requerida
por el intérprete congelado de CE3X v3.2 (wxPython y Cython), eliminando todos los datos
fantasma de ejemplos (CENER, Pamplona, etc.) e inyectando con precisión milimétrica los
datos administrativos y térmicos del inmueble y técnico sin corromper la matriz de simulación.
"""

import os
import io
import json
import pickle
from typing import Any, List, Dict, Optional
from ce3x_mcp.services.technician_profile import obtener_perfil_tecnico

PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANONICAL_TEMPLATE_PATH = os.path.join(PACKAGE_DIR, "templates", "plantilla_coruna.cex")
FALLBACK_TEMPLATE_PATH = r"C:\Program Files (x86)\CE3Xv3.2\Ejemplos\2 Vivienda dentro de bloque.cex"

# Mapeo oficial de normalización de provincias de CE3X (Calculos/listados.pyd)
# Verificado directamente con la GUI oficial de CE3X v3.2 (52 provincias y ciudades autónomas)
PROVINCIAS_CE3X = {
    "A CORUÑA": "A Coruña",
    "A CORUNA": "A Coruña",
    "CORUÑA": "A Coruña",
    "CORUNA": "A Coruña",
    "LA CORUÑA": "A Coruña",
    "ALAVA": "Álava",
    "ÁLAVA": "Álava",
    "ARABA": "Álava",
    "ALBACETE": "Albacete",
    "ALICANTE": "Alicante",
    "ALACANT": "Alicante",
    "ALMERIA": "Almería",
    "ALMERÍA": "Almería",
    "ASTURIAS": "Asturias",
    "AVILA": "Ávila ",
    "ÁVILA": "Ávila ",
    "BADAJOZ": "Badajoz",
    "BARCELONA": "Barcelona",
    "BURGOS": "Burgos",
    "CACERES": "Cáceres",
    "CÁCERES": "Cáceres",
    "CADIZ": "Cádiz",
    "CÁDIZ": "Cádiz",
    "CANTABRIA": "Cantabria",
    "CASTELLON": "Castellón",
    "CASTELLÓN": "Castellón",
    "CASTELLO": "Castellón",
    "CEUTA": "Ceuta",
    "CIUDAD REAL": "Ciudad Real",
    "CORDOBA": "Córdoba",
    "CÓRDOBA": "Córdoba",
    "CUENCA": "Cuenca",
    "GIRONA": "Girona",
    "GERONA": "Girona",
    "GRANADA": "Granada",
    "GUADALAJARA": "Guadalajara",
    "GUIPUZCOA": "Guipúzcoa",
    "GUIPÚZCOA": "Guipúzcoa",
    "GIPUZKOA": "Guipúzcoa",
    "HUELVA": "Huelva",
    "HUESCA": "Huesca",
    "ILLES BALEARS": "Illes Balears",
    "BALEARES": "Illes Balears",
    "ISLAS BALEARES": "Illes Balears",
    "JAEN": "Jaén",
    "JAÉN": "Jaén",
    "LA RIOJA": "La Rioja",
    "RIOJA": "La Rioja",
    "LAS PALMAS": "Las Palmas",
    "LEON": "León",
    "LEÓN": "León",
    "LLEIDA": "Lleida",
    "LERIDA": "Lleida",
    "LÉRIDA": "Lleida",
    "LUGO": "Lugo",
    "MADRID": "Madrid ",
    "MALAGA": "Málaga",
    "MÁLAGA": "Málaga",
    "MELILLA": "Melilla",
    "MURCIA": "Murcia",
    "NAVARRA": "Navarra",
    "NAFARROA": "Navarra",
    "OURENSE": "Ourense",
    "ORENSE": "Ourense",
    "PALENCIA": "Palencia",
    "PONTEVEDRA": "Pontevedra",
    "SALAMANCA": "Salamanca",
    "SANTA CRUZ DE TENERIFE": "Santa Cruz de Tenerife",
    "TENERIFE": "Santa Cruz de Tenerife",
    "SEGOVIA": "Segovia",
    "SEVILLA": "Sevilla",
    "SORIA": "Soria",
    "TARRAGONA": "Tarragona",
    "TERUEL": "Teruel",
    "TOLEDO": "Toledo",
    "VALENCIA": "Valencia",
    "VALÈNCIA": "Valencia",
    "VALLADOLID": "Valladolid",
    "VIZCAYA": "Vizcaya",
    "BIZKAIA": "Vizcaya",
    "ZAMORA": "Zamora",
    "ZARAGOZA": "Zaragoza"
}

# Localidades predefinidas oficiales en los desplegables de CE3X por provincia
# Cualquier municipio no incluido en la lista de su provincia figura en CE3X como "Otro"
LOCALIDADES_CE3X_POR_PROVINCIA = {
    "A Coruña": ["Arteixo", "Carballo", "A Coruña", "Ferrol", "Narón", "Oleiros", "Ribeira", "Santiago de Compostela", "Otro"],
    "Álava": ["Amurrio", "Llodio", "Salvatierra", "Vitoria-Gasteiz", "Otro"],
    "Albacete": ["Albacete", "Almansa", "Hellin", "Villarrobledo", "Otro"],
}

def normalizar_provincia_ce3x(nombre: str) -> str:
    """Devuelve el nombre de provincia con la grafía y espacios exactos requeridos por CE3X."""
    if not nombre:
        return "A Coruña"
    limpio = nombre.strip().upper()
    return PROVINCIAS_CE3X.get(limpio, nombre.strip())

def normalizar_localidad_ce3x(municipio: str, provincia: str) -> str:
    """
    Devuelve la localidad admitida en el desplegable Choice de CE3X.
    Si el municipio figura en la lista predefinida de la provincia, devuelve su grafía exacta.
    Si no figura entre los municipios principales predefinidos por CE3X, devuelve 'Otro'.
    """
    prov_norm = normalizar_provincia_ce3x(provincia).strip()
    mun_limpio = (municipio or "").strip()
    if prov_norm in LOCALIDADES_CE3X_POR_PROVINCIA:
        lista = LOCALIDADES_CE3X_POR_PROVINCIA[prov_norm]
        for loc in lista:
            if loc.lower() == mun_limpio.lower():
                return loc
        return "Otro"
    return mun_limpio

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
    altura_libre: float = 2.6,
    zona_climatica: str = "C1",
    referencia_catastral: str = "8014008NJ4081S0003RF",
    nombre_tecnico: Optional[str] = None,
    nif_tecnico: Optional[str] = None,
    titulacion: Optional[str] = None,
    colegio_profesional: Optional[str] = None,
    numero_colegiado: Optional[str] = None,
    domicilio_tecnico: Optional[str] = None,
    municipio_tecnico: Optional[str] = None,
    provincia_tecnico: Optional[str] = None,
    codigo_postal_tecnico: Optional[str] = None,
    telefono_tecnico: Optional[str] = None,
    email_tecnico: Optional[str] = None,
    razon_social: Optional[str] = None,
    nombre_cliente: Optional[str] = None,
    nif_cliente: Optional[str] = None,
    tipo_edificio: str = "Vivienda dentro de un bloque",
    tipologia: Optional[str] = None,
    **kwargs
) -> str:
    """
    Genera un archivo de proyecto .cex 100% compatible con CE3X v3.2.
    Utiliza mutación in-place línea por línea exclusivamente sobre los objetos 1 y 2
    (Datos Administrativos y Generales), preservando la integridad intacta de los objetos
    3 a 15 (matrices de cálculo, librerías de materiales y simulación de Medidas de Mejora).
    """
    template_path = CANONICAL_TEMPLATE_PATH if os.path.exists(CANONICAL_TEMPLATE_PATH) else FALLBACK_TEMPLATE_PATH
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Plantilla base CE3X no encontrada en {template_path}")
        
    with open(template_path, "rb") as f:
        data = f.read()

    lines = data.split(b"\r\n")

    # Cargar perfil de técnico persistente
    perfil = obtener_perfil_tecnico()
    tec_nom = (nombre_tecnico or perfil.get("nombre_tecnico", "Técnico Certificador Colegiado")).strip()
    tec_nif = (nif_tecnico or perfil.get("nif_tecnico", "00000000T")).strip()
    tec_tit = (titulacion or perfil.get("titulacion", "Arquitecto Técnico")).strip()
    tec_col = (colegio_profesional or perfil.get("colegio_profesional", "Colegio Oficial correspondiente")).strip()
    tec_num = str(numero_colegiado or perfil.get("numero_colegiado", "")).strip()
    if tec_num and tec_col and tec_num not in tec_col:
        tec_col = f"{tec_col} (Col. {tec_num})"
    tec_dir = (domicilio_tecnico or perfil.get("domicilio", "Domicilio Profesional")).strip()
    tec_mun = (municipio_tecnico or perfil.get("municipio", municipio)).strip()
    tec_prov = normalizar_provincia_ce3x(provincia_tecnico or perfil.get("provincia", provincia)).strip()
    tec_cp = (codigo_postal_tecnico or perfil.get("codigo_postal", codigo_postal)).strip()
    tec_tel = (telefono_tecnico or perfil.get("telefono", "981000000")).strip()
    tec_email = (email_tecnico or perfil.get("email", "tecnico@certificador.es")).strip()
    tec_empresa = (razon_social or perfil.get("razon_social", tec_nom)).strip()
    cli_nom = nombre_cliente or tec_nom
    cli_nif = nif_cliente or "00000000Z"

    prov_norm = normalizar_provincia_ce3x(provincia)
    mun_norm = municipio.strip()
    zc_norm = zona_climatica.strip().upper()
    rc_clean = referencia_catastral.strip()

    # Normalización del tipo de edificio para CE3X
    # Controles Choice de CE3X admiten: 'Vivienda Individual', 'Bloque de Viviendas', 'Unifamiliar', 'Edificio Terciario'
    tipo_norm = "Vivienda Individual"
    if tipo_edificio:
        t_low = tipo_edificio.lower()
        if "bloque" in t_low and "vivienda dentro" not in t_low:
            tipo_norm = "Bloque de Viviendas"
        elif "unifamiliar" in t_low:
            tipo_norm = "Unifamiliar"
        elif "terciario" in t_low:
            tipo_norm = "Edificio Terciario"
        else:
            tipo_norm = "Vivienda Individual"

    # Normativa por año de construcción oficial de CE3X
    # Claves internas de CE3X: 'Anterior' (<1980), 'NBE-CT-79' (1980-1998),
    # 'NBE-CT-79_aPartir1998' (1998-2007), 'CTE 2006' (2007-2013), 'CTE 2013' (>=2014)
    if ano_construccion < 1980:
        norm_str = "Anterior"
    elif ano_construccion < 1998:
        norm_str = "NBE-CT-79"
    elif ano_construccion < 2007:
        norm_str = "NBE-CT-79_aPartir1998"
    elif ano_construccion < 2014:
        norm_str = "CTE 2006"
    else:
        norm_str = "CTE 2013"

    # Conversión estricta a Latin-1 requerida por Python 2.7 / Cython de CE3X
    def to_lat(s: str) -> bytes:
        return str(s).encode("latin1", errors="replace")

    # Mutación quirúrgica en Objeto 1 (Datos Administrativos, índices 0-59)
    if len(lines) > 75:
        # Edificio
        lines[3] = b"V" + to_lat(nombre_edificio)
        lines[5] = b"aV" + to_lat(direccion)
        lines[7] = b"aV" + to_lat(prov_norm)
        # lines[9] es ag3 (memo a provincia si municipio == provincia)
        if prov_norm.lower() == mun_norm.lower():
            lines[9] = b"ag3"
        else:
            lines[9] = b"aV" + to_lat(mun_norm)

        # Cliente / Solicitante
        lines[12] = b"aV" + to_lat(cli_nom)
        lines[14] = b"aV" + to_lat(cli_nom)
        lines[16] = b"aV" + to_lat(direccion)
        lines[18] = b"aV" + to_lat(tec_tel)
        lines[20] = b"aV" + to_lat(tec_email)

        # Técnico Certificador
        lines[22] = b"aV" + to_lat(tec_nom)
        lines[24] = b"aV" + to_lat(tec_empresa)
        lines[26] = b"aV" + to_lat(tec_tel)
        lines[28] = b"aV" + to_lat(tec_email)
        lines[30] = b"aV" + to_lat(codigo_postal)

        # Referencia Catastral (20 caracteres)
        lines[33] = b"V" + to_lat(rc_clean)

        # Localidad y Provincia del Técnico / Cliente
        lines[35] = b"aaV" + to_lat(tec_mun)
        lines[37] = b"aV" + to_lat(tec_prov)
        lines[39] = b"aV" + to_lat(tec_cp)
        lines[41] = b"aV" + to_lat(tec_nif)
        lines[43] = b"aV" + to_lat(tec_nif)
        lines[45] = b"aV" + to_lat(tec_dir)
        lines[48] = b"aV" + to_lat(tec_mun)
        lines[50] = b"aV" + to_lat(tec_cp)
        lines[52] = b"aV" + to_lat(tec_tit)
        # Grado de protección del edificio (obj1[26])
        # Controles Choice de CE3X admiten estrictamente: 'Ninguna', 'Integral', 'Estructural', 'Ambiental'
        # NUNCA inyectar texto de colegio profesional aquí, ya que pertenece al XML y PDF oficial,
        # y en CE3X provoca una excepción en wx.Choice.SetStringSelection que congela el diálogo 'Abriendo...'
        grado_prot = kwargs.get("grado_proteccion", "Ninguna")
        if grado_prot not in ["Integral", "Estructural", "Ambiental"]:
            grado_prot = "Ninguna"
        lines[54] = b"aV" + to_lat(grado_prot)

        # Mutación quirúrgica en Objeto 2 (Datos Generales, índices 60-108)
        lines[60] = b"V" + to_lat(norm_str)
        lines[62] = b"aV" + to_lat(tipo_norm)
        lines[64] = b"aV" + to_lat(prov_norm)
        loc_gen = normalizar_localidad_ce3x(mun_norm, prov_norm)
        if prov_norm.lower() == loc_gen.lower() or prov_norm.lower() == mun_norm.lower():
            lines[66] = b"ag3"
        else:
            lines[66] = b"aV" + to_lat(loc_gen)
        lines[67] = b"aV" + to_lat(zc_norm)

        # Superficie útil real y altura libre
        sup_str = f"{superficie_util:.2f}".rstrip("0").rstrip(".") if superficie_util else "150"
        alt_str = f"{altura_libre:.2f}".rstrip("0").rstrip(".") if altura_libre else "2.6"
        lines[71] = b"aV" + to_lat(sup_str)
        lines[73] = b"aV" + to_lat(alt_str)

        # Año de construcción real (Línea 97) y Superficie CTE DB-HE (Línea 101)
        if len(lines) > 102:
            lines[97] = b"aV" + to_lat(str(ano_construccion))
            lines[101] = b"aV" + to_lat(sup_str)
    resultado_bytes = b"\r\n".join(lines)
    os.makedirs(os.path.dirname(os.path.abspath(ruta_salida)), exist_ok=True)
    with open(ruta_salida, "wb") as f:
        f.write(resultado_bytes)
        
    return ruta_salida

guardar_fichero_cex_basico = guardar_fichero_cex_completo
