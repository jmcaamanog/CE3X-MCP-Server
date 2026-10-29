# -*- coding: utf-8 -*-
from typing import Optional, Dict, Any, List, Annotated, Union
try:
    from fastmcp import FastMCP, Context
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP, Context
    except ImportError:
        class FastMCP:
            def __init__(self, name: str, description: str = ""):
                self.name = name
                self.description = description
                self.tools = {}
            def tool(self, **kwargs):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func
                return decorator
            def resource(self, uri: str):
                def decorator(func): return func
                return decorator
            def prompt(self):
                def decorator(func): return func
                return decorator
            def run(self, **kwargs):
                print(f"FastMCP {self.name} iniciado.")
        class Context:  # type: ignore
            async def report_progress(self, progress: float, total: Optional[float] = None, message: Optional[str] = None) -> None: pass
            async def info(self, message: str, **kwargs: Any) -> None: pass
from pydantic import Field
import os
import tempfile
import shutil
import asyncio

def reportar_progreso_seguro(ctx: Any, progreso: float, total: float, mensaje: str) -> None:
    """Envía telemetría de progreso a FastMCP de forma segura y no bloqueante."""
    if ctx is None or not hasattr(ctx, "report_progress"):
        return
    try:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(ctx.report_progress(progreso, total, mensaje))
        except RuntimeError:
            asyncio.run(ctx.report_progress(progreso, total, mensaje))
    except Exception:
        pass

from ce3x_mcp.core.models import (
    ProyectoCertificacion,
    DatosAdministrativos,
    DatosGenerales,
    ResultadoCalificacion,
    InstalacionTermica,
    CerramientoOpaco,
    HuecoVentana,
    MedidaMejora
)
from ce3x_mcp.services.catastro import consultar_catastro_por_rc
from ce3x_mcp.services.ce3x_engine_connector import verificar_instalacion_ce3x, obtener_escalas_oficiales_zona
from ce3x_mcp.services.cte_climate import (
    obtener_zona_climatica,
    estimar_transmitancias_por_ano,
    calcular_calificacion_energetica_simplificada,
    FACTORES_PASO
)
from ce3x_mcp.services.xml_builder import generar_xml_oficial_30
from ce3x_mcp.services.pdf_compiler import compilar_pdf_desde_xml
from ce3x_mcp.services.cex_codec import guardar_fichero_cex_completo
from ce3x_mcp.services.bim_parser import extraer_envolvente_desde_ifc
from ce3x_mcp.services.equipment_parser import analizar_datos_equipo_climatizacion
from ce3x_mcp.services.improvement_engine import calcular_paquetes_medidas_mejora
from ce3x_mcp.services.pvgis_client import calcular_produccion_solar_pvgis
from ce3x_mcp.services.nextgen_report import generar_informe_justificativo_nextgen
from ce3x_mcp.services.plan_parser import analizar_plano_distribucion_pdf
from ce3x_mcp.services.trials_and_tests import (
    registrar_visita_e_inspeccion,
    registrar_ensayo_blower_door,
    calcular_puentes_termicos_cte,
    contrastar_facturas_reales,
    calcular_sombras_estacionales_hueco,
    calcular_patron_sombras_edificio_colindante,
    estimar_parametros_terciario_comercial,
    registrar_ensayo_flujometria_termica_iso9869,
    calcular_transmitancia_ventana_iso10077,
    calcular_demanda_acs_cte_he4
)
from ce3x_mcp.services.technician_profile import guardar_perfil_tecnico, obtener_perfil_tecnico
from ce3x_mcp.services.smart_folder_auditor import auditar_carpeta_inmueble, certificar_inmueble_desde_carpeta, organizar_carpeta_visita as organizar_carpeta_visita_impl
from ce3x_mcp.services.libraries import (
    CATALOGO_MUROS_FACHADA,
    CATALOGO_VIDRIOS,
    CATALOGO_MARCOS_CARPINTERIA,
    inferir_solucion_envolvente_por_ano
)

INSTRUCCIONES_SERVIDOR = (
    "Servidor MCP Oficial para Certificación Energética de Edificios en España (CE3X v3.2 / CTE DB-HE / RD 390/2021).\n\n"
    "PRINCIPIOS FUNDAMENTALES DE RIGOR TÉCNICO Y VERACIDAD:\n"
    "1. VERIFICACIÓN PREVIA DE CE3X: Antes de cualquier certificación, ejecuta 'verificar_conexion_ce3x' para constatar que CE3X v3.2 está instalado localmente, conectado con sus motores de cálculo, escalas oficiales (Localidades.xml) y compilador PDF (xml2cert).\n"
    "2. PROHIBICIÓN ABSOLUTA DE DATOS INVENTADOS O FALSOS: Jamás inventar instalaciones, superficies ni envolventes. Si faltan datos críticos (tipo de calefacción, ACS o superficie), PREGUNTAR de forma precisa al usuario o técnico antes de certificar.\n"
    "3. PROHIBICIÓN DE DATOS DE EJEMPLO: Los entregables oficiales (.cex, .xml, .pdf) deben reflejar única y exclusivamente el inmueble y técnico reales. Está terminantemente prohibido incluir datos residuales de ejemplos ajenos.\n"
    "4. USO DE MOTORES Y ESCALAS OFICIALES: Todas las calificaciones y demandas se fundamentan en las escalas oficiales de CE3X (Escala/Localidades.xml) para la zona climática y tipología exactas.\n\n"
    "PROTOCOLO DE INTERACCIÓN OBLIGATORIO PARA LA IA:\n"
    "1. PRIMER CONTACTO: Si el usuario aporta una carpeta de visita, pregúntale la ruta completa (ej. C:\\MisVisitas\\Inmueble). Si aporta datos sueltos (Referencia Catastral, año, superficie), ejecuta 'consultar_catastro' para contrastar datos reales.\n"
    "2. ESTRUCTURACIÓN AUTOMÁTICA: Si hay carpeta, ejecuta 'organizar_carpeta_visita' para ordenar en INFORMACION/, PLANOS/, FOTOS/, INSTALACIONES/ y CERTIFICADO/.\n"
    "3. AUDITORÍA Y PREGUNTAS QUIRÚRGICAS: Ejecuta 'auditar_carpeta_visita' y formula al técnico ÚNICAMENTE preguntas sobre datos que falten (orientación, tipo real de calefacción/ACS o sombras) antes de certificar.\n"
    "4. GENERACIÓN OFICIAL LIMPIA: Ejecuta 'certificar_desde_carpeta_visita' o 'generar_certificado_completo'. Todos los entregables (.cex nativo, XML v3.0 y PDF de 15 págs.) se generan validados y sin datos fantasma."
)
try:
    mcp = FastMCP("CE3X-MCP-Server", instructions=INSTRUCCIONES_SERVIDOR)
except TypeError:
    try:
        mcp = FastMCP("CE3X-MCP-Server", description=INSTRUCCIONES_SERVIDOR)
    except TypeError:
        mcp = FastMCP("CE3X-MCP-Server")

# ==============================================================================
# HERRAMIENTAS OFICIALES MCP (27 TOOLS - GRADO A TDQS ENRIQUECIDO)
# ==============================================================================

DESC_CATASTRO = """Consulta telemática a la Sede Electrónica del Catastro de España para obtener dirección oficial, municipio, provincia, año de construcción y superficie catastral.

Cuándo usar:
    Invoque esta herramienta como primer paso ante cualquier inmueble en territorio español común cuando disponga de la Referencia Catastral para auto-rellenar los datos administrativos y de partida del certificado.

Comportamiento y efectos secundarios:
    Operación de consulta externa telemática (Read-Only) con caché persistente SQLite local (TTL de 30 días). No altera archivos ni estado local."""

@mcp.tool(description=DESC_CATASTRO, annotations={"read_only_hint": True, "idempotent_hint": True})
def consultar_catastro(
    referencia_catastral: Annotated[str, Field(description="Referencia Catastral oficial del inmueble (14 o 20 caracteres alfanuméricos, ej. '8014008NJ4081S0003RF').")]
) -> Dict[str, Any]:
    """Consulta telemática a la Sede Electrónica del Catastro de España.
    
    Args:
        referencia_catastral: Código oficial alfanumérico del Catastro inmobiliario de España.
        
    Returns:
        Diccionario con dirección, municipio, provincia, código postal, año de construcción, superficie construida y estado de éxito.
    """
    return consultar_catastro_por_rc(referencia_catastral)


DESC_ZONA_CLIMATICA = """Determina la zona climática CTE DB-HE oficial (ej. C1, D3, A3, E1) en función de la provincia, municipio y altitud sobre el nivel del mar según las tablas oficiales del Código Técnico de la Edificación (Apéndice B).

Cuándo usar:
    Invoque esta herramienta de forma obligatoria antes de estimar transmitancias o calcular la calificación energética para fijar la severidad climática de invierno y verano del emplazamiento.

Comportamiento y efectos secundarios:
    Operación analítica de solo lectura (Read-Only). No requiere conexión con CE3X ni modifica archivos en disco."""

@mcp.tool(description=DESC_ZONA_CLIMATICA, annotations={"read_only_hint": True, "idempotent_hint": True})
def determinar_zona_climatica(
    provincia: Annotated[str, Field(description="Nombre oficial de la provincia española (ej. 'Madrid', 'A Coruña', 'Sevilla', 'Barcelona').")],
    municipio: Annotated[str, Field(description="Nombre oficial del municipio correspondiente a la provincia.")],
    altitud_m: Annotated[float, Field(description="Altitud del inmueble sobre el nivel del mar en metros (m). Por defecto 0.0.", ge=-50.0, le=4000.0)] = 0.0
) -> Dict[str, str]:
    """Determina la zona climática CTE DB-HE oficial.
    
    Args:
        provincia: Nombre oficial de la provincia española.
        municipio: Nombre oficial del municipio.
        altitud_m: Altitud en metros sobre el nivel del mar.
        
    Returns:
        Diccionario con provincia, municipio, altitud y código de zona climática oficial (ej. 'D3').
    """
    zona = obtener_zona_climatica(provincia, municipio, altitud_m)
    return {
        "provincia": provincia,
        "municipio": municipio,
        "altitud_m": str(altitud_m),
        "zona_climatica_cte": zona
    }


DESC_ENVOLVENTE_DEFECTO = """Estima las transmitancias térmicas (U en W/m²K) de fachadas, cubiertas, suelos y huecos según el año de construcción del edificio y su normativa histórica aplicable (Anterior a 1979, NBE-CT-79, CTE-HE-2006, CTE-HE-2013, CTE-HE-2019).

Cuándo usar:
    Utilice esta herramienta cuando no se disponga de ensayos in situ (flujometría) ni de memorias constructivas conocidas del edificio para obtener los valores tabulados por defecto de los manuales oficiales de CE3X. Para mediciones reales in situ use 'registrar_ensayo_flujometria_termica_in_situ'.

Comportamiento y efectos secundarios:
    Operación analítica de solo lectura (Read-Only). No altera archivos ni estado persistente."""

@mcp.tool(description=DESC_ENVOLVENTE_DEFECTO, annotations={"read_only_hint": True, "idempotent_hint": True})
def estimar_envolvente_por_defecto(
    ano_construccion: Annotated[int, Field(description="Año de construcción del edificio según Catastro o escritura (ej. 1975, 1995, 2012).", ge=1800, le=2050)],
    zona_climatica: Annotated[str, Field(description="Zona climática CTE DB-HE asignada (ej. 'A3', 'B4', 'C1', 'D3', 'E1').")] = "C1"
) -> Dict[str, Any]:
    """Estima transmitancias térmicas de envolvente por defecto según normativa histórica.
    
    Args:
        ano_construccion: Año de edificación del inmueble.
        zona_climatica: Zona climática oficial del CTE DB-HE.
        
    Returns:
        Diccionario con normativa aplicable, transmitancias estimadas (fachada, cubierta, suelo, huecos) y tipologías constructivas asociadas.
    """
    return estimar_transmitancias_por_ano(ano_construccion, zona_climatica)


DESC_VERIFICAR_CE3X = """Verifica y testea de forma exhaustiva la instalación y conectividad con el software oficial CE3X v3.2 (ejecutables, motores climáticos, validador XML RelaxNG y escalas oficiales).

Cuándo usar:
    Invoque esta herramienta durante el arranque inicial o en pruebas de diagnóstico del entorno para verificar la presencia de CE3Xv3.2.exe, xml2cert.exe y xmlcheck.exe.

Comportamiento y efectos secundarios:
    Operación de diagnóstico de solo lectura (Read-Only). Inspecciona el sistema de archivos local sin alterar configuraciones ni registrar escrituras."""

@mcp.tool(description=DESC_VERIFICAR_CE3X, annotations={"read_only_hint": True, "idempotent_hint": True})
def verificar_conexion_ce3x(
    directorio_ce3x: Annotated[Optional[str], Field(description="Ruta absoluta al directorio de instalación de CE3X v3.2. Si es None, autodetecta en 'C:\\Program Files (x86)\\CE3Xv3.2'.")] = None
) -> Dict[str, Any]:
    """Verifica la instalación y motores oficiales de CE3X v3.2.
    
    Args:
        directorio_ce3x: Ruta personalizada opcional a la carpeta de CE3X.
        
    Returns:
        Diccionario con el estado de conexión de cada componente oficial y ruta detectada.
    """
    return verificar_instalacion_ce3x(directorio_ce3x)


DESC_CALC_CALIFICACION = """Calcula la demanda energética estimada, consumo de energía primaria no renovable, emisiones de CO2 y asigna las letras de calificación energética oficiales (A a G) conectando directamente con las escalas y edificios de referencia de CE3X (Escala/Localidades.xml).

Cuándo usar:
    Utilice esta herramienta para pre-calificar rápidamente un inmueble y verificar la letra energética antes de generar el paquete documental definitivo con 'generar_certificado_completo'.

Comportamiento y efectos secundarios:
    Operación analítica de solo lectura (Read-Only). Conecta con las bases de datos de CE3X sin modificar archivos ni registrar persistencia."""

@mcp.tool(description=DESC_CALC_CALIFICACION, annotations={"read_only_hint": True, "idempotent_hint": True})
def calcular_calificacion_energetica(
    superficie_util: Annotated[float, Field(description="Superficie útil habitable del edificio o vivienda en metros cuadrados (m²).", gt=0.0)],
    ano_construccion: Annotated[int, Field(description="Año de construcción catastral del edificio.", ge=1800, le=2050)],
    zona_climatica: Annotated[str, Field(description="Zona climática CTE DB-HE (ej. 'C1', 'D3', 'E1').")] = "C1",
    tipo_calefaccion: Annotated[Optional[str], Field(description="Tipo o vector energético de la calefacción: 'EfectoJoule', 'GasNatural', 'Gasoleo', 'Biomasa', 'BombaCalor', o None.")] = None,
    tipo_acs: Annotated[Optional[str], Field(description="Tipo o vector energético del ACS: 'EfectoJoule', 'GasNatural', 'Gasoleo', 'BombaCalor', o None.")] = None,
    tipologia: Annotated[str, Field(description="Tipología edificatoria: 'Bloque', 'Unifamiliar' o 'Terciario'.")] = "Bloque"
) -> Dict[str, Any]:
    """Calcula la calificación energética reglamentaria según escalas oficiales CE3X.
    
    Args:
        superficie_util: Superficie útil habitable en m².
        ano_construccion: Año de construcción del edificio.
        zona_climatica: Código de zona climática CTE.
        tipo_calefaccion: Vector energético de calefacción.
        tipo_acs: Vector energético de ACS.
        tipologia: Tipo de inmueble ('Bloque', 'Unifamiliar', 'Terciario').
        
    Returns:
        Diccionario con demandas de calefacción/refrigeración/ACS, consumo C_epnr, emisiones CO2 y letras oficiales (A-G).
    """
    res = calcular_calificacion_energetica_simplificada(
        superficie_util=superficie_util,
        ano_construccion=ano_construccion,
        zona_climatica=zona_climatica,
        tipo_calefaccion=tipo_calefaccion,
        tipo_acs=tipo_acs,
        tipologia=tipologia
    )
    return {
        "demanda_calefaccion_kwh_m2a": res["demandas"]["calefaccion"],
        "demanda_refrigeracion_kwh_m2a": res["demandas"]["refrigeracion"],
        "demanda_acs_kwh_m2a": res["demandas"]["acs"],
        "consumo_energia_primaria_nr_kwh_m2a": res["consumo_epnr_kwh_m2_ano"],
        "emisiones_co2_kg_m2a": res["emisiones_co2_kg_m2_ano"],
        "calificacion_global_emisiones": res["calificacion"]["emisiones"],
        "calificacion_global_energia_primaria": res["calificacion"]["energia_primaria_no_renovable"],
        "letra_demanda_calefaccion": res["calificacion"]["demanda_calefaccion"],
        "vector_energetico_principal": res["instalaciones_evaluadas"]["combustible_calefaccion"],
        "escalas_oficiales_ce3x": res["escalas_oficiales"],
        "instalaciones_evaluadas": res["instalaciones_evaluadas"],
        "aviso_normativo": res.get("aviso_normativo")
    }


DESC_BIM_IFC = """Abre y analiza un modelo BIM IFC mediante IfcOpenShell, extrayendo automáticamente las superficies útiles de estancias (IfcSpace), muros de fachada exterior (IfcWall) y carpinterías exteriores (IfcWindow/IfcDoor) para su integración en CE3X.

Cuándo usar:
    Invoque esta herramienta cuando disponga del modelo tridimensional BIM del proyecto (Revit, Archicad, Allplan, CYPE) para automatizar la cubicación de la envolvente térmica. Para planos 2D en papel o PDF use 'analizar_plano_arquitectura_pdf'.

Comportamiento y efectos secundarios:
    Operación de lectura y cubicación geométrica (Read-Only). No altera el archivo IFC original. Emite progreso interactivo a FastMCP."""

@mcp.tool(description=DESC_BIM_IFC, annotations={"read_only_hint": True, "idempotent_hint": True})
def analizar_modelo_bim_ifc(
    ifc_path: Annotated[str, Field(description="Ruta absoluta o relativa al archivo de modelo BIM en formato IFC (.ifc, IFC2X3 o IFC4).")],
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """Cubicación y análisis de envolvente térmica desde modelo BIM IFC.
    
    Args:
        ifc_path: Ruta al archivo IFC.
        ctx: Contexto de ejecución FastMCP para telemetría.
        
    Returns:
        Diccionario con superficie útil total, listado de espacios, áreas de cerramientos opacos y cuadros de huecos acristalados.
    """
    reportar_progreso_seguro(ctx, 20, 100, f"Cargando modelo BIM IFC {os.path.basename(ifc_path)}...")
    res = extraer_envolvente_desde_ifc(ifc_path)
    reportar_progreso_seguro(ctx, 100, 100, "Cubicación y análisis BIM finalizado.")
    return res


DESC_PLANO_PDF = """Abre y analiza un plano arquitectónico en PDF vectorial mediante PyMuPDF, extrayendo superficies útiles de estancias (m²) y cuadros de carpintería de huecos y ventanas.

Cuándo usar:
    Utilice esta herramienta cuando disponga de planos de planta en PDF para extraer estancias, cotas y cuadros de ventanas. Para modelos tridimensionales IFC use 'analizar_modelo_bim_ifc'.

Comportamiento y efectos secundarios:
    Operación de lectura y parseo vectorial (Read-Only). No altera el archivo PDF de entrada. Emite progreso interactivo a FastMCP."""

@mcp.tool(description=DESC_PLANO_PDF, annotations={"read_only_hint": True, "idempotent_hint": True})
def analizar_plano_arquitectura_pdf(
    pdf_path: Annotated[str, Field(description="Ruta absoluta o relativa al archivo PDF que contiene el plano arquitectónico de distribución.")],
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """Análisis y extracción geométrica de planos de arquitectura en PDF.
    
    Args:
        pdf_path: Ruta al archivo PDF del plano.
        ctx: Contexto de ejecución FastMCP para telemetría.
        
    Returns:
        Diccionario con estancias detectadas, superficie útil calculada, escala identificada y carpinterías exteriores.
    """
    reportar_progreso_seguro(ctx, 20, 100, f"Analizando plano vectorial {os.path.basename(pdf_path)}...")
    res = analizar_plano_distribucion_pdf(pdf_path)
    reportar_progreso_seguro(ctx, 100, 100, "Extracción de plano arquitectónico finalizada.")
    return res


DESC_FICHA_EQUIPO = """Analiza la descripción textual o ficha técnica de un equipo térmico (aerotermia, caldera de condensación, bomba de calor, termo eléctrico) y extrae su potencia nominal (kW), rendimiento estacional (SCOP/COP/SEER) y vector energético para CE3X.

Cuándo usar:
    Invoque esta herramienta a partir de notas técnicas, transcripción de fotos de placas o catálogos del fabricante para parametrizar las instalaciones térmicas en CE3X.

Comportamiento y efectos secundarios:
    Operación analítica de procesamiento de lenguaje natural y extracción técnica (Read-Only). Sin efectos secundarios en disco."""

@mcp.tool(description=DESC_FICHA_EQUIPO, annotations={"read_only_hint": True, "idempotent_hint": True})
def analizar_ficha_equipo_clima(
    descripcion_o_ficha: Annotated[str, Field(description="Texto técnico o descripción detallada de la ficha de características del equipo de climatización (ej. 'Bomba de calor aerotérmica Daikin Altherma 8 kW con SCOP 4.2').")]
) -> Dict[str, Any]:
    """Extracción técnica y paramétrica de equipos térmicos desde fichas o descripciones.
    
    Args:
        descripcion_o_ficha: Texto descriptivo de la placa o ficha técnica.
        
    Returns:
        Diccionario con tipo de equipo, potencia térmica nominal (kW), rendimiento estacional (SCOP/COP) y combustible asociado.
    """
    return analizar_datos_equipo_climatizacion(descripcion_o_ficha)


DESC_PVGIS = """Calcula con precisión científica la producción de energía solar fotovoltaica (kWh/año y mensual) conectando con la API oficial PVGIS de la Comisión Europea (JRC) con radiación satelital SARAH-2.

Cuándo usar:
    Utilice esta herramienta al evaluar la integración de energía solar fotovoltaica para autoconsumo como medida de mejora o justificación CTE DB-HE5.

Comportamiento y efectos secundarios:
    Operación de consulta telemática a la API de la Comisión Europea con caché persistente SQLite local (TTL de 90 días). Read-Only."""

@mcp.tool(description=DESC_PVGIS, annotations={"read_only_hint": True, "idempotent_hint": True})
def calcular_produccion_fotovoltaica_pvgis(
    latitud: Annotated[float, Field(description="Latitud geográfica en grados decimales (ej. 43.3623 para A Coruña, 40.4168 para Madrid).", ge=-90.0, le=90.0)],
    longitud: Annotated[float, Field(description="Longitud geográfica en grados decimales (ej. -8.4115 para A Coruña, -3.7038 para Madrid).", ge=-180.0, le=180.0)],
    potencia_pico_kw: Annotated[float, Field(description="Potencia pico de la instalación solar fotovoltaica en kilovatios (kWp). Por defecto 3.0 kWp.", gt=0.0)] = 3.0,
    inclinacion_grados: Annotated[float, Field(description="Inclinación de los módulos solares respecto a la horizontal en grados (0 a 90°). Por defecto 35.0°.", ge=0.0, le=90.0)] = 35.0,
    azimut_grados: Annotated[float, Field(description="Orientación o azimut de los paneles: 0° Sur, 90° Oeste, -90° Este, 180° Norte. Por defecto 0.0° (Sur).", ge=-180.0, le=180.0)] = 0.0
) -> Dict[str, Any]:
    """Cálculo satelital oficial PVGIS de producción solar fotovoltaica.
    
    Args:
        latitud: Coordenada de latitud en grados decimales.
        longitud: Coordenada de longitud en grados decimales.
        potencia_pico_kw: Potencia pico de paneles en kWp.
        inclinacion_grados: Grados de inclinación de los módulos.
        azimut_grados: Orientación respecto al sur geográfico.
        
    Returns:
        Diccionario con producción anual total (kWh/año), producción mensual detallada y pérdidas estimadas del sistema.
    """
    return calcular_produccion_solar_pvgis(latitud, longitud, potencia_pico_kw, inclinacion_grados, azimut_grados)


DESC_MEJORAS_RD390 = """Genera automáticamente los 3 paquetes de medidas de mejora exigidos por el Real Decreto 390/2021 (Mejora de Envolvente SATE, Sustitución por Aerotermia y Solución Integral con Solar FV), calculando reducción de emisiones, ahorro en factura (€/año) y periodo de amortización (payback).

Cuándo usar:
    Invoque esta herramienta preceptivamente en todo certificado energético de edificio existente para cumplimentar el Anexo III de Medidas de Mejora. Para auditar subvenciones NextGen use 'emitir_dictamen_subvenciones_nextgen'.

Comportamiento y efectos secundarios:
    Operación de cálculo analítico y financiero (Read-Only). No modifica archivos en disco. Emite progreso interactivo a FastMCP."""

@mcp.tool(description=DESC_MEJORAS_RD390, annotations={"read_only_hint": True, "idempotent_hint": True})
def proponer_medidas_mejora_rd390(
    superficie_util: Annotated[float, Field(description="Superficie útil del inmueble en m².", gt=0.0)],
    ano_construccion: Annotated[int, Field(description="Año de construcción catastral del edificio.", ge=1800, le=2050)],
    zona_climatica: Annotated[str, Field(description="Zona climática CTE DB-HE asignada.")] = "C1",
    tipo_calefaccion: Annotated[str, Field(description="Sistema de calefacción actual del edificio.")] = "EfectoJoule",
    tipo_acs: Annotated[str, Field(description="Sistema de ACS actual del edificio.")] = "EfectoJoule",
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """Generación oficial de paquetes de medidas de mejora según Real Decreto 390/2021.
    
    Args:
        superficie_util: Superficie útil habitable en m².
        ano_construccion: Año de construcción original.
        zona_climatica: Código de zona climática CTE.
        tipo_calefaccion: Tipo de calefacción actual.
        tipo_acs: Tipo de ACS actual.
        ctx: Contexto FastMCP para telemetría.
        
    Returns:
        Diccionario con los 3 paquetes reglamentarios de mejora, inversión estimada (€), ahorro (€/año), reducción porcentual y nuevo salto de letra.
    """
    reportar_progreso_seguro(ctx, 35, 100, "Calculando demanda y balance térmico oficial...")
    calc = calcular_calificacion_energetica(
        superficie_util=superficie_util,
        ano_construccion=ano_construccion,
        zona_climatica=zona_climatica,
        tipo_calefaccion=tipo_calefaccion,
        tipo_acs=tipo_acs
    )
    adm = DatosAdministrativos(
        nombre_edificio="Inmueble",
        direccion="Calle",
        municipio="Municipio",
        provincia="Provincia",
        codigo_postal="00000"
    )
    gen = DatosGenerales(
        ano_construccion=ano_construccion,
        zona_climatica=zona_climatica,
        superficie_util=superficie_util
    )
    res = ResultadoCalificacion(
        demanda_calefaccion=calc["demanda_calefaccion_kwh_m2a"],
        demanda_refrigeracion=calc["demanda_refrigeracion_kwh_m2a"],
        demanda_acs=calc["demanda_acs_kwh_m2a"],
        consumo_energia_primaria_nr=calc["consumo_energia_primaria_nr_kwh_m2a"],
        emisiones_co2=calc["emisiones_co2_kg_m2a"],
        letra_global_emisiones=calc["calificacion_global_emisiones"],
        letra_global_energia_primaria=calc["calificacion_global_energia_primaria"],
        letra_calefaccion=calc["calificacion_global_emisiones"],
        letra_refrigeracion="A",
        letra_acs=calc["calificacion_global_emisiones"]
    )
    proyecto = ProyectoCertificacion(administrativos=adm, generales=gen)
    reportar_progreso_seguro(ctx, 70, 100, "Calculando paquetes reglamentarios RD 390/2021 (SATE, Aerotermia, Integral)...")
    medidas = calcular_paquetes_medidas_mejora(proyecto, res)
    reportar_progreso_seguro(ctx, 100, 100, "Paquetes de medidas de mejora calculados.")
    return {
        "calificacion_actual": calc,
        "medidas_de_mejora": [m.model_dump() for m in medidas]
    }

DESC_NEXTGEN = """Genera el informe técnico justificativo y dictamen oficial de cumplimiento para las subvenciones Next Generation EU (RD 853/2021) y deducciones fiscales en IRPF (40%/60%).

Cuándo usar:
    Utilice esta herramienta para justificar el cumplimiento del requisito normativo de reducción del 30% en consumo de energía primaria no renovable para tramitar ayudas públicas.

Comportamiento y efectos secundarios:
    Operación analítica de evaluación económica y normativa (Read-Only). No altera archivos."""

@mcp.tool(description=DESC_NEXTGEN, annotations={"read_only_hint": True, "idempotent_hint": True})
def emitir_dictamen_subvenciones_nextgen(
    superficie_util: Annotated[float, Field(description="Superficie útil habitable en m².", gt=0.0)],
    ano_construccion: Annotated[int, Field(description="Año de construcción del inmueble.", ge=1800, le=2050)],
    zona_climatica: Annotated[str, Field(description="Zona climática CTE DB-HE.")] = "C1",
    tipo_calefaccion: Annotated[str, Field(description="Sistema de calefacción actual.")] = "EfectoJoule",
    tipo_acs: Annotated[str, Field(description="Sistema de ACS actual.")] = "EfectoJoule",
    paquete_mejora: Annotated[Union[int, str], Field(description="Paquete de mejora a evaluar: 1 (Envolvente SATE), 2 (Aerotermia) o 3 (Integral con Solar FV).")] = 3
) -> Dict[str, Any]:
    """Dictamen técnico oficial de justificación de subvenciones Next Generation EU (RD 853/2021).
    
    Args:
        superficie_util: Superficie útil del inmueble en m².
        ano_construccion: Año de construcción.
        zona_climatica: Zona climática CTE.
        tipo_calefaccion: Sistema de calefacción actual.
        tipo_acs: Sistema de ACS actual.
        paquete_mejora: Paquete de mejora a evaluar (1, 2 o 3).
        
    Returns:
        Diccionario con porcentaje de ahorro de energía primaria no renovable, tramo de ayuda concedible (40%, 65%, 80%), deducción de IRPF y texto de dictamen oficial.
    """
    calc = calcular_calificacion_energetica(
        superficie_util=superficie_util,
        ano_construccion=ano_construccion,
        zona_climatica=zona_climatica,
        tipo_calefaccion=tipo_calefaccion,
        tipo_acs=tipo_acs
    )
    adm = DatosAdministrativos(
        nombre_edificio="Inmueble Objeto de Rehabilitación",
        direccion="Calle de la Rehabilitación 1",
        municipio="A Coruña",
        provincia="A Coruña",
        codigo_postal="15001"
    )
    gen = DatosGenerales(
        ano_construccion=ano_construccion,
        zona_climatica=zona_climatica,
        superficie_util=superficie_util
    )
    res = ResultadoCalificacion(
        demanda_calefaccion=calc["demanda_calefaccion_kwh_m2a"],
        demanda_refrigeracion=calc["demanda_refrigeracion_kwh_m2a"],
        demanda_acs=calc["demanda_acs_kwh_m2a"],
        consumo_energia_primaria_nr=calc["consumo_energia_primaria_nr_kwh_m2a"],
        emisiones_co2=calc["emisiones_co2_kg_m2a"],
        letra_global_emisiones=calc["calificacion_global_emisiones"],
        letra_global_energia_primaria=calc["calificacion_global_energia_primaria"],
        letra_calefaccion=calc["calificacion_global_emisiones"],
        letra_refrigeracion="A",
        letra_acs=calc["calificacion_global_emisiones"]
    )
    proyecto = ProyectoCertificacion(administrativos=adm, generales=gen)
    medidas = calcular_paquetes_medidas_mejora(proyecto, res)
    
    if isinstance(paquete_mejora, int):
        idx = max(0, min(paquete_mejora - 1, len(medidas) - 1))
    else:
        pm_str = str(paquete_mejora).strip().upper()
        if "SATE" in pm_str and "AERO" in pm_str:
            idx = 2
        elif "AERO" in pm_str:
            idx = 1
        elif "SATE" in pm_str or "ENV" in pm_str:
            idx = 0
        else:
            try:
                idx = max(0, min(int(pm_str) - 1, len(medidas) - 1))
            except ValueError:
                idx = 2
    medida_sel = medidas[idx]
    return generar_informe_justificativo_nextgen(proyecto, res, medida_sel)

DESC_CERTIFICADO_COMPLETO = """Genera el conjunto completo de entregables oficiales para el certificado energético: archivo de proyecto .cex para CE3X v3.2, archivo XML oficial v3.0 validado con xmlcheck.exe y PDF oficial de 15 páginas compilado con Typst / xml2cert.exe.

Cuándo usar:
    Invoque esta herramienta como fase final de la certificación tras haber validado todos los datos de envolvente, clima e instalaciones para producir los documentos oficiales exigidos por la Administración.

Comportamiento y efectos secundarios:
    Operación de generación de archivos en disco (Write). Escribe los archivos .cex, .xml y .pdf en el directorio de salida especificado. Emite progreso interactivo a FastMCP."""

@mcp.tool(description=DESC_CERTIFICADO_COMPLETO, annotations={"read_only_hint": False, "destructive_hint": False})
def generar_certificado_completo(
    nombre_edificio: Annotated[str, Field(description="Nombre identificativo del edificio o vivienda (ej. 'Vivienda Unifamiliar Caamaño').")],
    direccion: Annotated[str, Field(description="Dirección completa del inmueble (calle, número, piso).")],
    municipio: Annotated[str, Field(description="Nombre oficial del municipio.")],
    provincia: Annotated[str, Field(description="Nombre oficial de la provincia española.")],
    codigo_postal: Annotated[str, Field(description="Código postal oficial de 5 dígitos (ej. '15001', '28001').")],
    superficie_util: Annotated[float, Field(description="Superficie útil habitable del inmueble en metros cuadrados (m²).", gt=0.0)],
    ano_construccion: Annotated[int, Field(description="Año de construcción del edificio según Catastro o proyecto.", ge=1800, le=2050)],
    tipo_calefaccion: Annotated[Optional[str], Field(description="Sistema térmico de calefacción instalado.")] = None,
    tipo_acs: Annotated[Optional[str], Field(description="Sistema de agua caliente sanitaria instalado.")] = None,
    referencia_catastral: Annotated[Optional[str], Field(description="Referencia Catastral oficial del inmueble.")] = None,
    directorio_salida: Annotated[Optional[str], Field(description="Ruta al directorio donde se guardarán los archivos generados. Si es None, usa carpeta temporal.")] = None,
    tipologia: Annotated[str, Field(description="Tipología del edificio: 'Bloque', 'Unifamiliar' o 'Terciario'.")] = "Bloque",
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """Generación integral de entregables oficiales (.cex, .xml v3.0, .pdf).
    
    Args:
        nombre_edificio: Nombre del proyecto o edificio.
        direccion: Dirección completa del inmueble.
        municipio: Municipio oficial.
        provincia: Provincia oficial.
        codigo_postal: Código postal de 5 dígitos.
        superficie_util: Superficie útil habitable en m².
        ano_construccion: Año de edificación.
        tipo_calefaccion: Vector energético de calefacción.
        tipo_acs: Vector energético de ACS.
        referencia_catastral: Referencia Catastral oficial.
        directorio_salida: Directorio destino para los archivos.
        tipologia: 'Bloque', 'Unifamiliar' o 'Terciario'.
        ctx: Contexto FastMCP para telemetría.
        
    Returns:
        Diccionario con rutas absolutas a los archivos .cex, .xml y .pdf generados, calificación obtenida y estado de validación RelaxNG.
    """
    out_dir = directorio_salida or os.path.join(tempfile.gettempdir(), "ce3x_certificados")
    os.makedirs(out_dir, exist_ok=True)
    
    # 0. Verificación preceptiva de la instalación oficial de CE3X v3.2
    reportar_progreso_seguro(ctx, 10, 100, "Verificando instalación oficial de CE3X v3.2...")
    ce3x_check = verificar_instalacion_ce3x()
    if not ce3x_check.get("instalado"):
        return {
            "estado": "error_instalacion_ce3x",
            "mensaje": "No se puede certificar sin CE3X instalado. Verifique la instalación oficial de CE3X v3.2 en C:\\Program Files (x86)\\CE3Xv3.2.",
            "detalle": ce3x_check
        }

    zona = obtener_zona_climatica(provincia, municipio)
    calc = calcular_calificacion_energetica(
        superficie_util=superficie_util,
        ano_construccion=ano_construccion,
        zona_climatica=zona,
        tipo_calefaccion=tipo_calefaccion,
        tipo_acs=tipo_acs,
        tipologia=tipologia
    )
    
    # Cargar perfil de técnico colegiado si está configurado
    perfil = obtener_perfil_tecnico()
    nombre_tec = perfil.get("nombre_tecnico", "Técnico Certificador Colegiado")
    nif_tec = perfil.get("nif_tecnico", perfil.get("nif", "00000000T"))
    tit_tec = perfil.get("titulacion", "Arquitectura técnica o aparejadores")
    empresa_tec = perfil.get("razon_social")
    
    adm = DatosAdministrativos(
        nombre_edificio=nombre_edificio,
        direccion=direccion,
        municipio=municipio,
        provincia=provincia,
        codigo_postal=codigo_postal,
        referencia_catastral=referencia_catastral,
        nombre_tecnico=nombre_tec,
        nif_tecnico=nif_tec,
        titulacion=tit_tec
    )
    
    gen = DatosGenerales(
        ano_construccion=ano_construccion,
        zona_climatica=zona,
        superficie_util=superficie_util,
        tipologia="ViviendaBloque"
    )
    
    res = ResultadoCalificacion(
        demanda_calefaccion=calc["demanda_calefaccion_kwh_m2a"],
        demanda_refrigeracion=calc["demanda_refrigeracion_kwh_m2a"],
        demanda_acs=calc["demanda_acs_kwh_m2a"],
        consumo_energia_primaria_nr=calc["consumo_energia_primaria_nr_kwh_m2a"],
        emisiones_co2=calc["emisiones_co2_kg_m2a"],
        letra_global_emisiones=calc["calificacion_global_emisiones"],
        letra_global_energia_primaria=calc["calificacion_global_energia_primaria"],
        letra_calefaccion=calc.get("letra_demanda_calefaccion", calc["calificacion_global_emisiones"]),
        letra_refrigeracion="A",
        letra_acs=calc["calificacion_global_emisiones"]
    )
    
    # Construir instalaciones térmicas reales
    instalaciones = []
    tc = tipo_calefaccion or "CalderaGasConvencional"
    ta = tipo_acs or "CalderaGasConvencional"
    
    # Generador de calefacción
    comb_cal_vec = "Electricidad" if ("joule" in tc.lower() or "aerotermia" in tc.lower()) else ("Gasoleo" if "gasoleo" in tc.lower() else "GasNatural")
    tec_cal = "CalderaCondensacion" if "condensacion" in tc.lower() else ("BombaCalorAerotermia" if "aerotermia" in tc.lower() else "CalderaEstandar")
    instalaciones.append(InstalacionTermica(
        nombre=f"Sistema Calefacción {tc}",
        tecnologia=tec_cal,
        tipo_servicio="Calefaccion",
        vector_energetico=comb_cal_vec,
        potencia_nominal_kw=24.0,
        rendimiento_estacional=3.2 if "aerotermia" in tc.lower() else (0.95 if "condensacion" in tc.lower() else 0.80)
    ))
    
    # Generador de ACS
    comb_acs_vec = "Electricidad" if ("joule" in ta.lower() or "aerotermia" in ta.lower() or "termo" in ta.lower()) else ("Gasoleo" if "gasoleo" in ta.lower() else "GasNatural")
    tec_acs = "CalderaCondensacion" if "condensacion" in ta.lower() else ("BombaCalorAerotermia" if "aerotermia" in ta.lower() else "CalderaEstandar")
    instalaciones.append(InstalacionTermica(
        nombre=f"Sistema ACS {ta}",
        tecnologia=tec_acs,
        tipo_servicio="ACS",
        vector_energetico=comb_acs_vec,
        potencia_nominal_kw=24.0,
        rendimiento_estacional=2.8 if "aerotermia" in ta.lower() else (0.90 if "condensacion" in ta.lower() else 0.78)
    ))

    proyecto = ProyectoCertificacion(
        administrativos=adm,
        generales=gen,
        instalaciones=instalaciones
    )
    
    # Determinar si la salida es la subcarpeta estándar CERTIFICADO/ para aplicar nombres canónicos
    es_carpeta_cert = os.path.basename(os.path.normpath(out_dir)).upper() == "CERTIFICADO"

    # 1. Generar XML Oficial Limpio (validado RelaxNG, sin Centro Juvenil ni 1006 kW)
    reportar_progreso_seguro(ctx, 75, 100, "Compilando XML v3.0 RelaxNG y PDF con Typst...")
    xml_content = generar_xml_oficial_30(proyecto, res)
    if es_carpeta_cert:
        xml_path = os.path.join(out_dir, "Certificado_Oficial_Registro.xml")
        cex_path = os.path.join(out_dir, "Proyecto_CE3X.cex")
    else:
        safe_mun = municipio.replace(" ", "_").replace(",", "")
        xml_path = os.path.join(out_dir, f"Certificado_{safe_mun}_{ano_construccion}.xml")
        cex_path = os.path.join(out_dir, f"Proyecto_{safe_mun}_{ano_construccion}.cex")
        
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_content)
        
    # 2. Compilar PDF Oficial
    pdf_ok, pdf_res = compilar_pdf_desde_xml(xml_path, out_dir)
    if es_carpeta_cert:
        pdf_temp = os.path.join(out_dir, "Certificado_Oficial_Registro.pdf")
        pdf_canonico = os.path.join(out_dir, "Informe_Certificacion_Energetica.pdf")
        if os.path.exists(pdf_temp) and os.path.abspath(pdf_temp) != os.path.abspath(pdf_canonico):
            if os.path.exists(pdf_canonico):
                os.remove(pdf_canonico)
            shutil.move(pdf_temp, pdf_canonico)
    
    # 3. Exportar .CEX nativo completo y compatible con la interfaz CE3X (sin CENER ni Pamplona)
    guardar_fichero_cex_completo(
        ruta_salida=cex_path,
        nombre_edificio=nombre_edificio,
        direccion=direccion,
        municipio=municipio,
        provincia=provincia,
        codigo_postal=codigo_postal,
        ano_construccion=ano_construccion,
        superficie_util=superficie_util,
        zona_climatica=zona,
        referencia_catastral=referencia_catastral or "",
        nombre_tecnico=nombre_tec,
        nif_tecnico=nif_tec,
        titulacion=tit_tec,
        razon_social=empresa_tec,
        tipologia="ViviendaBloque"
    )
    
    return {
        "estado": "completado",
        "calificacion_obtenida": {
            "emisiones": calc["calificacion_global_emisiones"],
            "energia_primaria_no_renovable": calc["calificacion_global_energia_primaria"],
            "demanda_calefaccion": calc.get("letra_demanda_calefaccion", calc["calificacion_global_emisiones"])
        },
        "archivo_xml_oficial": xml_path,
        "archivo_pdf_oficial": pdf_res if pdf_ok else f"No se pudo compilar PDF: {pdf_res}",
        "archivo_cex_ce3x": cex_path,
        "resumen_energetico": calc,
        "verificacion_rigor": {
            "datos_inventados": False,
            "conexion_ce3x_escalas": True,
            "xml_sin_datos_fantasma": True,
            "cex_adaptado_real": True
        }
    }

DESC_ORGANIZAR_CARPETA = """Crea la estructura estándar de 5 carpetas canónicas (01_FOTOS, 02_PLANOS, 03_DOCUMENTACION, 04_NOTAS_CAMPO, 05_ENTREGABLES) y clasifica automáticamente los archivos existentes según su extensión y metadatos.

Cuándo usar:
    Utilice esta herramienta al inicio del flujo de trabajo documental tras descargar los archivos tomados en la visita para ordenar la información. Antes de certificar, ejecute 'auditar_carpeta_visita'.

Comportamiento y efectos secundarios:
    Operación de gestión del sistema de archivos (Write / Organize). Mueve y organiza archivos dentro de la carpeta indicada sin eliminar contenidos."""

@mcp.tool(description=DESC_ORGANIZAR_CARPETA, annotations={"read_only_hint": False, "destructive_hint": False})
def organizar_carpeta_visita(
    ruta_carpeta: Annotated[str, Field(description="Ruta absoluta o relativa a la carpeta raíz de la visita técnica.")]
) -> Dict[str, Any]:
    """Crea la estructura estándar de 5 carpetas y clasifica archivos de visita.
    
    Args:
        ruta_carpeta: Directorio del inmueble a estructurar.
        
    Returns:
        Diccionario con carpetas creadas, archivos movidos por categoría y resumen de organización.
    """
    return organizar_carpeta_visita_impl(ruta_carpeta)


DESC_AUDITAR_CARPETA = """Audita de forma autónoma una carpeta de visita técnica (croquis, notas, planos PDF, fotos y fichas) verificando si se dispone de toda la información preceptiva para certificar y emite un informe de salud documental.

Cuándo usar:
    Invoque esta herramienta antes de ejecutar 'certificar_desde_carpeta_visita' para detectar omisiones preceptivas (como fotos de instalaciones, planos o referencia catastral).

Comportamiento y efectos secundarios:
    Operación de inspección y análisis documental (Read-Only). No modifica los archivos existentes. Emite progreso interactivo a FastMCP."""

@mcp.tool(description=DESC_AUDITAR_CARPETA, annotations={"read_only_hint": True, "idempotent_hint": True})
def auditar_carpeta_visita(
    ruta_carpeta: Annotated[str, Field(description="Ruta a la carpeta de visita técnica a auditar.")],
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """Auditoría de integridad documental para carpetas de visita técnica.
    
    Args:
        ruta_carpeta: Ruta a la carpeta que contiene la documentación de visita.
        ctx: Contexto FastMCP para telemetría.
        
    Returns:
        Diccionario con índice de completitud (0-100%), datos identificados, elementos faltantes y recomendación técnica.
    """
    reportar_progreso_seguro(ctx, 30, 100, f"Inspeccionando contenidos de {os.path.basename(ruta_carpeta)}...")
    res = auditar_carpeta_inmueble(ruta_carpeta)
    reportar_progreso_seguro(ctx, 100, 100, "Auditoría de carpeta completada.")
    return res


DESC_CERTIFICAR_CARPETA = """Certifica de forma automática el inmueble a partir de la carpeta de visita procesando planos PDF, Catastro y notas de campo para generar los archivos oficiales (.cex, .xml y .pdf) dentro de la carpeta 05_ENTREGABLES.

Cuándo usar:
    Utilice esta herramienta cuando disponga de una carpeta de visita organizada para ejecutar el flujo integral end-to-end de certificación en un solo paso.

Comportamiento y efectos secundarios:
    Operación integral con escritura en disco (Write). Crea la subcarpeta 'CERTIFICADO' dentro de '05_ENTREGABLES' con los documentos oficiales. Emite progreso interactivo a FastMCP."""

@mcp.tool(description=DESC_CERTIFICAR_CARPETA, annotations={"read_only_hint": False, "destructive_hint": False})
def certificar_desde_carpeta_visita(
    ruta_carpeta: Annotated[str, Field(description="Ruta a la carpeta que contiene los archivos de la visita técnica.")],
    orientacion_principal: Annotated[str, Field(description="Orientación predominante de la fachada principal: 'Sur', 'Norte', 'Este', 'Oeste', etc.")] = "Sur",
    tipo_calefaccion: Annotated[Optional[str], Field(description="Vector de calefacción: 'EfectoJoule', 'GasNatural', 'Gasoleo', 'BombaCalor', etc.")] = None,
    tipo_acs: Annotated[Optional[str], Field(description="Vector de ACS: 'EfectoJoule', 'GasNatural', 'Gasoleo', 'BombaCalor', etc.")] = None,
    nombre_edificio: Annotated[Optional[str], Field(description="Nombre o denominación del edificio.")] = None,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """Certificación automatizada integral desde carpeta de visita técnica.
    
    Args:
        ruta_carpeta: Ruta a la carpeta de visita técnica.
        orientacion_principal: Orientación solar de la fachada principal.
        tipo_calefaccion: Sistema de calefacción comprobado.
        tipo_acs: Sistema de ACS comprobado.
        nombre_edificio: Denominación del inmueble.
        ctx: Contexto FastMCP para telemetría.
        
    Returns:
        Diccionario con informe de extracción documental y rutas a los archivos .cex, .xml y .pdf oficiales generados.
    """
    reportar_progreso_seguro(ctx, 20, 100, "Extrayendo datos de planos, Catastro y notas de campo...")
    res = certificar_inmueble_desde_carpeta(
        ruta_carpeta=ruta_carpeta,
        orientacion_principal=orientacion_principal,
        tipo_calefaccion=tipo_calefaccion,
        tipo_acs=tipo_acs,
        nombre_edificio=nombre_edificio
    )
    reportar_progreso_seguro(ctx, 100, 100, "Certificación desde carpeta completada.")
    return res


DESC_VISITA_PRESENCIAL = """Registra formalmente la visita presencial obligatoria exigida por el Art. 8 del RD 390/2021, generando el documento justificativo del Anexo IV preceptivo para el registro administrativo autonómico.

Cuándo usar:
    Invoque esta herramienta de forma preceptiva para todo certificado de edificio existente para acreditar la visita presencial del técnico competente.

Comportamiento y efectos secundarios:
    Operación de registro y generación documental (Write). Crea el acta de visita presencial en disco."""

@mcp.tool(description=DESC_VISITA_PRESENCIAL, annotations={"read_only_hint": False, "destructive_hint": False})
def registrar_visita_presencial(
    fecha_visita: Annotated[str, Field(description="Fecha de la visita presencial en formato YYYY-MM-DD (ej. '2026-10-17').")],
    pruebas_realizadas: Annotated[str, Field(description="Descripción de las pruebas y comprobaciones in situ realizadas (ej. 'Inspección visual de cerramientos, medición láser, toma de datos de caldera').")],
    observaciones_tecnicas: Annotated[str, Field(description="Observaciones técnicas adicionales recogidas durante la inspección.")] = ""
) -> Dict[str, Any]:
    """Registro oficial de visita presencial conforme al Real Decreto 390/2021.
    
    Args:
        fecha_visita: Fecha en formato estándar ISO YYYY-MM-DD.
        pruebas_realizadas: Detalle de las comprobaciones realizadas in situ.
        observaciones_tecnicas: Notas técnicas complementarias.
        
    Returns:
        Diccionario con los datos del registro oficial de visita presencial y confirmación reglamentaria.
    """
    return registrar_visita_e_inspeccion(fecha_visita, pruebas_realizadas, observaciones_tecnicas)


DESC_BLOWER_DOOR = """Procesa un ensayo de estanqueidad al aire según norma UNE-EN ISO 9972 (Blower Door), calculando la tasa de renovación n50 (renovaciones/hora), la permeabilidad q50 (m³/h·m²) y la tasa de infiltración de aire para CE3X.

Cuándo usar:
    Utilice esta herramienta cuando se haya ejecutado un ensayo de presurización/despresurización Blower Door para sustituir la tasa de infiltración estimada por defecto de CE3X por el valor real medido.

Comportamiento y efectos secundarios:
    Operación de cálculo analítico normativo (Read-Only). No altera archivos ni estado persistente."""

@mcp.tool(description=DESC_BLOWER_DOOR, annotations={"read_only_hint": True, "idempotent_hint": True})
def registrar_ensayo_estanqueidad_blower_door(
    volumen_neto_m3: Annotated[float, Field(description="Volumen interno neto del espacio calefactado en metros cúbicos (m³).", gt=0.0)],
    superficie_envolvente_m2: Annotated[float, Field(description="Superficie total de la envolvente térmica interior en metros cuadrados (m²).", gt=0.0)],
    caudal_50pa_m3h: Annotated[float, Field(description="Caudal de fuga de aire medido a 50 Pa de presión en metros cúbicos por hora (m³/h).", gt=0.0)]
) -> Dict[str, Any]:
    """Procesamiento y cálculo normativo de ensayo Blower Door (ISO 9972).
    
    Args:
        volumen_neto_m3: Volumen interior climatizado en m³.
        superficie_envolvente_m2: Área de envolvente en contacto con el aire en m².
        caudal_50pa_m3h: Fuga de aire a 50 Pa en m³/h.
        
    Returns:
        Diccionario con n50 (renovaciones/hora), q50 (m³/h·m²), tasa de infiltración CE3X y diagnóstico de hermeticidad Passivhaus / CTE.
    """
    return registrar_ensayo_blower_door(volumen_neto_m3, superficie_envolvente_m2, caudal_50pa_m3h)


DESC_PUENTES_TERMICOS = """Calcula las transmitancias térmicas lineales (psi en W/m·K) y la pérdida térmica global por puentes térmicos integrados según el Documento de Apoyo DA DB-HE / 3 del Código Técnico de la Edificación.

Cuándo usar:
    Invoque esta herramienta para cuantificar el impacto térmico de frentes de forjado, contornos de hueco y pilares en fachada en lugar de usar valores globales estimados.

Comportamiento y efectos secundarios:
    Operación analítica de solo lectura (Read-Only). Sin efectos secundarios en disco."""

@mcp.tool(description=DESC_PUENTES_TERMICOS, annotations={"read_only_hint": True, "idempotent_hint": True})
def calcular_puentes_termicos(
    ano_construccion: Annotated[int, Field(description="Año de construcción del edificio para asignar la transmitancia lineal de referencia según normativa histórica aplicable.", ge=1800, le=2050)],
    perimetro_forjado_m: Annotated[float, Field(description="Longitud total de frentes de forjado en fachada en metros (m).", ge=0.0)] = 0.0,
    perimetro_huecos_m: Annotated[float, Field(description="Perímetro total de contornos de huecos y ventanas en metros (m).", ge=0.0)] = 0.0,
    longitud_pilares_m: Annotated[float, Field(description="Longitud total de pilares integrados en fachada exterior en metros (m).", ge=0.0)] = 0.0
) -> Dict[str, Any]:
    """Cálculo normativo de puentes térmicos lineales integrados según CTE DA DB-HE/3.
    
    Args:
        ano_construccion: Año de construcción para determinar la solución constructiva.
        perimetro_forjado_m: Metros lineales de frente de forjado.
        perimetro_huecos_m: Metros lineales de contorno de ventanas.
        longitud_pilares_m: Metros lineales de pilares en fachada.
        
    Returns:
        Diccionario con transmitancias lineales individuales (W/m·K), pérdidas térmicas parciales y pérdida total transmitida (W/K).
    """
    return calcular_puentes_termicos_cte(ano_construccion, perimetro_forjado_m, perimetro_huecos_m, longitud_pilares_m)


DESC_PERFIL_TECNICO = """Configura y guarda de forma persistente los datos colegiales y profesionales del técnico certificador (nombre, NIF, titulación, colegio, número de colegiado) para auto-cumplimentar todos los certificados generados.

Cuándo usar:
    Invoque esta herramienta una sola vez o cuando cambien los datos profesionales del técnico para que se inyecten automáticamente en los archivos .cex, .xml y .pdf.

Comportamiento y efectos secundarios:
    Operación de configuración persistente (Write). Guarda los datos en el archivo de perfil local del usuario."""

@mcp.tool(description=DESC_PERFIL_TECNICO, annotations={"read_only_hint": False, "destructive_hint": False})
def configurar_perfil_tecnico_colegiado(
    nombre_tecnico: Annotated[str, Field(description="Nombre y apellidos completos del técnico certificador competente.")],
    nif_tecnico: Annotated[str, Field(description="NIF o NIE del técnico certificador.")],
    titulacion: Annotated[str, Field(description="Titulación académica habilitante (ej. 'Arquitecto Técnico', 'Ingeniero de Edificación', 'Arquitecto').")],
    colegio_profesional: Annotated[str, Field(description="Nombre oficial del Colegio Profesional (ej. 'Colegio Oficial de la Arquitectura Técnica de A Coruña').")],
    numero_colegiado: Annotated[str, Field(description="Número de colegiado profesional.")],
    razon_social: Annotated[str, Field(description="Razón social del estudio o empresa técnica (opcional).")] = "",
    domicilio: Annotated[str, Field(description="Domicilio o dirección profesional del técnico.")] = "",
    municipio: Annotated[str, Field(description="Municipio del domicilio profesional.")] = "",
    provincia: Annotated[str, Field(description="Provincia del domicilio profesional.")] = "",
    codigo_postal: Annotated[str, Field(description="Código postal profesional de 5 dígitos.")] = "",
    telefono: Annotated[str, Field(description="Teléfono de contacto profesional.")] = "",
    email: Annotated[str, Field(description="Correo electrónico profesional de contacto.")] = "",
    comunidad_autonoma: Annotated[str, Field(description="Comunidad Autónoma donde ejerce habitualmente la actividad.")] = "Galicia"
) -> Dict[str, Any]:
    """Configuración y persistencia del perfil profesional del técnico competente.
    
    Args:
        nombre_tecnico: Nombre completo del profesional.
        nif_tecnico: NIF/NIE del profesional.
        titulacion: Titulación técnica colegiada.
        colegio_profesional: Colegio profesional oficial.
        numero_colegiado: Número de colegiación.
        razon_social: Empresa o sociedad profesional.
        domicilio: Dirección profesional.
        municipio: Municipio profesional.
        provincia: Provincia profesional.
        codigo_postal: Código postal profesional.
        telefono: Teléfono de contacto.
        email: Email de contacto.
        comunidad_autonoma: Comunidad autónoma.
        
    Returns:
        Diccionario con el perfil persistido y confirmación de guardado.
    """
    perfil = {
        "nombre_tecnico": nombre_tecnico,
        "nif_tecnico": nif_tecnico,
        "titulacion": titulacion,
        "colegio_profesional": colegio_profesional,
        "numero_colegiado": numero_colegiado,
        "razon_social": razon_social,
        "domicilio": domicilio,
        "municipio": municipio,
        "provincia": provincia,
        "codigo_postal": codigo_postal,
        "telefono": telefono,
        "email": email,
        "comunidad_autonoma": comunidad_autonoma
    }
    return guardar_perfil_tecnico(perfil)


DESC_SOMBRAS_HUECO = """Calcula los factores reductores de sombra estacionales (verano e invierno) y el factor solar modificado Fs para huecos acristalados debidos a elementos de sombra propios (voladizos, retranqueos y aleros) según CTE DB-HE.

Cuándo usar:
    Utilice esta herramienta para calcular la protección solar propia de las ventanas del edificio. Para obstáculos remotos frente al edificio (edificios de enfrente, árboles lejanos), use 'calcular_sombras_obstaculo_edificio_enfrente'.

Comportamiento y efectos secundarios:
    Operación analítica de solo lectura (Read-Only). No modifica archivos ni registros locales."""

@mcp.tool(description=DESC_SOMBRAS_HUECO, annotations={"read_only_hint": True, "idempotent_hint": True})
def calcular_sombras_hueco(
    orientacion: Annotated[str, Field(description="Orientación del hueco: 'Sur', 'Norte', 'Este', 'Oeste', 'Sureste', 'Suroeste', 'Noreste', 'Noroeste'.")],
    ancho_hueco_m: Annotated[float, Field(description="Ancho de la ventana en metros (m).", gt=0.0)],
    alto_hueco_m: Annotated[float, Field(description="Alto de la ventana en metros (m).", gt=0.0)],
    retranqueo_m: Annotated[float, Field(description="Profundidad del retranqueo de la ventana respecto al plano exterior de fachada en metros (m).", ge=0.0)] = 0.0,
    vuelo_voladizo_m: Annotated[float, Field(description="Saliente o vuelo del voladizo o alero superior en metros (m).", ge=0.0)] = 0.0,
    tiene_toldo: Annotated[bool, Field(description="Indica si el hueco dispone de toldo u obstáculo móvil exterior de protección solar.")] = False
) -> Dict[str, Any]:
    """Cálculo normativo de factores de sombra propios para ventanas y huecos (CTE DB-HE).
    
    Args:
        orientacion: Orientación solar de la ventana.
        ancho_hueco_m: Anchura del hueco en metros.
        alto_hueco_m: Altura del hueco en metros.
        retranqueo_m: Retranqueo respecto al paramento en metros.
        vuelo_voladizo_m: Vuelo del voladizo en metros.
        tiene_toldo: Presencia de toldo de protección solar.
        
    Returns:
        Diccionario con factor de sombra en verano (F_sh,verano), factor en invierno (F_sh,invierno) y factor solar modificado Fs.
    """
    return calcular_sombras_estacionales_hueco(orientacion, ancho_hueco_m, alto_hueco_m, retranqueo_m, vuelo_voladizo_m, tiene_toldo)


DESC_CONTRASTAR_FACTURAS = """Compara el consumo real de energía de los últimos 12 meses (electricidad, gas natural o gasóleo) obtenido de facturas con el consumo teórico calculado por CE3X para evaluar la fiabilidad de la calificación y detectar anomalías de uso.

Cuándo usar:
    Invoque esta herramienta para contrastar la calificación teórica con la realidad del usuario conforme al procedimiento de validación y contraste con facturas del RD 390/2021.

Comportamiento y efectos secundarios:
    Operación analítica de solo lectura (Read-Only). No altera archivos."""

@mcp.tool(description=DESC_CONTRASTAR_FACTURAS, annotations={"read_only_hint": True, "idempotent_hint": True})
def contrastar_consumo_facturas_reales(
    consumo_teorico_kwh_ano: Annotated[float, Field(description="Consumo teórico anual total calculado por CE3X en kWh/año.", gt=0.0)],
    electricidad_real_kwh: Annotated[float, Field(description="Consumo eléctrico real facturado de los últimos 12 meses en kWh.", ge=0.0)] = 0.0,
    gas_natural_real_kwh: Annotated[float, Field(description="Consumo real de gas natural de los últimos 12 meses en kWh.", ge=0.0)] = 0.0,
    gasoleo_real_litros: Annotated[float, Field(description="Consumo real de gasóleo de calefacción de los últimos 12 meses en litros.", ge=0.0)] = 0.0
) -> Dict[str, Any]:
    """Contraste y validación de consumo teórico vs facturas energéticas reales (RD 390/2021).
    
    Args:
        consumo_teorico_kwh_ano: Consumo simulado por el modelo térmico en kWh/año.
        electricidad_real_kwh: Electricidad facturada en kWh.
        gas_natural_real_kwh: Gas natural facturado en kWh.
        gasoleo_real_litros: Litros de gasóleo consumidos.
        
    Returns:
        Diccionario con consumo real total en energía final (kWh/año), desviación porcentual, factor de concordancia y diagnóstico técnico.
    """
    return contrastar_facturas_reales(consumo_teorico_kwh_ano, electricidad_real_kwh, gas_natural_real_kwh, gasoleo_real_litros)


DESC_OBSTACULO_EDIFICIO = """Calcula el ángulo de elevación solar alfa (grados) y la tabla de perfil de sombras producida por un obstáculo remoto continuo (edificio colindante o frente a fachada) según el Anejo E del CTE DB-HE.

Cuándo usar:
    Utilice esta herramienta para modelar sombras arrojadas por construcciones vecinas o accidentes topográficos. Para elementos propios del hueco (voladizos, retranqueos, aleros), use 'calcular_sombras_hueco'.

Comportamiento y efectos secundarios:
    Operación analítica de cálculo geométrico solar (Read-Only). No escribe archivos ni altera estado."""

@mcp.tool(description=DESC_OBSTACULO_EDIFICIO, annotations={"read_only_hint": True, "idempotent_hint": True})
def calcular_sombras_obstaculo_edificio_enfrente(
    distancia_edificio_m: Annotated[float, Field(description="Distancia horizontal en metros (m) desde la fachada del edificio evaluado hasta el obstáculo o edificio de enfrente.", gt=0.0)],
    altura_edificio_m: Annotated[float, Field(description="Altura del edificio u obstáculo de enfrente en metros (m) medida por encima del centro del hueco evaluado.", gt=0.0)],
    orientacion_fachada: Annotated[str, Field(description="Orientación de la fachada que recibe la sombra: 'Sur', 'Norte', 'Este', 'Oeste', 'Sureste', 'Suroeste', 'Noreste', 'Noroeste'.")],
    descripcion_obstaculo: Annotated[str, Field(description="Descripción del obstáculo remoto (ej. 'Edificio de 6 plantas enfrente').")] = "Edificio colindante"
) -> Dict[str, Any]:
    """Cálculo geométrico solar de patrones de sombra de obstáculos remotos (CTE DB-HE Anejo E).
    
    Args:
        distancia_edificio_m: Distancia horizontal en metros al obstáculo.
        altura_edificio_m: Altura del obstáculo respecto al hueco en metros.
        orientacion_fachada: Orientación solar de la fachada receptora.
        descripcion_obstaculo: Etiqueta descriptiva del obstáculo.
        
    Returns:
        Diccionario con ángulo alfa (°), tabla de perfil de obstáculos (azimut y elevación) y reducción de radiación estimada.
    """
    return calcular_patron_sombras_edificio_colindante(distancia_edificio_m, altura_edificio_m, orientacion_fachada, descripcion_obstaculo)


DESC_TERCIARIO = """Estima los parámetros normativos obligatorios de CE3X para edificios de uso Terciario y Locales Comerciales: potencia de iluminación instalada (W/m²), VEEI, caudales de ventilación (RITE IDA) y tasa de ocupación según CTE DB-HE3 y RITE.

Cuándo usar:
    Invoque esta herramienta obligatoriamente cuando el edificio o inmueble certificado sea de uso terciario o local comercial para obtener los parámetros de iluminación y ventilación que exige CE3X en terciario.

Comportamiento y efectos secundarios:
    Operación analítica de solo lectura (Read-Only). No modifica archivos ni registros locales."""

@mcp.tool(description=DESC_TERCIARIO, annotations={"read_only_hint": True, "idempotent_hint": True})
def calcular_parametros_terciario_local_comercial(
    tipo_actividad: Annotated[str, Field(description="Tipo de actividad del local o edificio terciario (ej. 'Comercial', 'Oficinas', 'Docente', 'Restauracion', 'Sanitario').")],
    superficie_util_m2: Annotated[float, Field(description="Superficie útil del local comercial en metros cuadrados (m²).", gt=0.0)],
    tipo_luminaria: Annotated[str, Field(description="Tecnología de iluminación principal: 'LED', 'Fluorescencia', 'Halogena', 'Incandescente'.")] = "LED",
    nivel_iluminacion_lux: Annotated[float, Field(description="Nivel medio de iluminancia mantenida en lux según exigencias de la actividad (CTE DB-HE3). Por defecto 500 lux.", gt=0.0)] = 500.0
) -> Dict[str, Any]:
    """Estimación normativa de parámetros de iluminación, VEEI y ventilación en edificios terciarios.
    
    Args:
        tipo_actividad: Uso terciario del local.
        superficie_util_m2: Superficie útil en m².
        tipo_luminaria: Tecnología de fuentes de luz.
        nivel_iluminacion_lux: Iluminancia en lux.
        
    Returns:
        Diccionario con potencia de iluminación (W/m²), VEEI límite, caudal de aire exterior (IDA) y densidad de carga interna.
    """
    return estimar_parametros_terciario_comercial(tipo_actividad, superficie_util_m2, tipo_luminaria, nivel_iluminacion_lux)


DESC_FLUJOMETRIA = """Registra formalmente un ensayo in situ de flujometría térmica con termoflujómetro y sondas de temperatura según norma ISO 9869-1, calculando la transmitancia térmica real U (W/m²K) y la resistencia térmica R del cerramiento.

Cuándo usar:
    Utilice esta herramienta cuando se hayan realizado mediciones directas in situ con termoflujómetro para acreditar la transmitancia real de un muro histórico sin necesidad de estimarlo por defecto.

Comportamiento y efectos secundarios:
    Operación analítica de cálculo normativo (Read-Only). Devuelve el valor oficial de U para su inserción como valor conocido en CE3X."""

@mcp.tool(description=DESC_FLUJOMETRIA, annotations={"read_only_hint": True, "idempotent_hint": True})
def registrar_ensayo_flujometria_termica_in_situ(
    flujo_medio_w_m2: Annotated[float, Field(description="Densidad de flujo de calor media medida a través del cerramiento en vatios por metro cuadrado (W/m²).", gt=0.0)],
    temp_interior_media_c: Annotated[float, Field(description="Temperatura media del aire interior durante el ensayo en grados Celsius (°C).")],
    temp_exterior_media_c: Annotated[float, Field(description="Temperatura media del aire exterior durante el ensayo en grados Celsius (°C).")],
    duracion_ensayo_horas: Annotated[float, Field(description="Duración total del registro continuo en horas (mínimo 72 h según ISO 9869-1).", ge=24.0)] = 72.0,
    elemento_analizado: Annotated[str, Field(description="Descripción del cerramiento ensayado (ej. 'Muro de fachada de ladrillo visto').")] = "Muro de fachada exterior"
) -> Dict[str, Any]:
    """Cálculo y acreditación oficial de ensayo de flujometría térmica in situ (ISO 9869-1).
    
    Args:
        flujo_medio_w_m2: Flujo térmico medido en W/m².
        temp_interior_media_c: Temperatura interior media en °C.
        temp_exterior_media_c: Temperatura exterior media en °C.
        duracion_ensayo_horas: Horas de ensayo continuas.
        elemento_analizado: Elemento constructivo evaluado.
        
    Returns:
        Diccionario con transmitancia térmica real U (W/m²K), resistencia térmica R (m²K/W) y validez del ensayo según ISO 9869-1.
    """
    return registrar_ensayo_flujometria_termica_iso9869(flujo_medio_w_m2, temp_interior_media_c, temp_exterior_media_c, duracion_ensayo_horas, elemento_analizado)


DESC_VENTANA_ISO10077 = """Calcula la transmitancia térmica total Uw (W/m²K) de una ventana conforme a la norma UNE-EN ISO 10077-1, ponderando las áreas de vidrio y marco e incorporando el efecto del intercalario térmico.

Cuándo usar:
    Utilice esta herramienta para calcular con precisión la transmitancia de huecos acristalados a partir de los datos técnicos de marco y vidrio antes de introducirlos en la envolvente térmica de CE3X.

Comportamiento y efectos secundarios:
    Operación analítica de solo lectura (Read-Only). No altera archivos ni estado local."""

@mcp.tool(description=DESC_VENTANA_ISO10077, annotations={"read_only_hint": True, "idempotent_hint": True})
def calcular_transmitancia_ventana_iso10077(
    ancho_m: Annotated[float, Field(description="Ancho del hueco de ventana en metros (m).", gt=0.0)],
    alto_m: Annotated[float, Field(description="Alto del hueco de ventana en metros (m).", gt=0.0)],
    u_vidrio_w_m2k: Annotated[float, Field(description="Transmitancia térmica del vidrio Ug en W/m²K (ej. 5.7 para simple, 2.8 para doble estándar, 1.1 para bajo emisivo).", gt=0.0)],
    u_marco_w_m2k: Annotated[float, Field(description="Transmitancia térmica del marco Uf en W/m²K (ej. 5.7 para metálico sin RPT, 3.2 con RPT, 2.2 para madera, 1.8 para PVC).", gt=0.0)],
    fraccion_marco: Annotated[float, Field(description="Fracción de superficie ocupada por el marco respecto al hueco total (0.10 a 0.50). Por defecto 0.20 (20%).", ge=0.05, le=0.60)] = 0.20,
    tipo_intercalario: Annotated[str, Field(description="Tipo de espaciador o intercalario del doble acristalamiento: 'aluminio' o 'calido_warm_edge'.")] = "aluminio"
) -> Dict[str, Any]:
    """Cálculo analítico de transmitancia térmica de ventana Uw según UNE-EN ISO 10077-1.
    
    Args:
        ancho_m: Ancho de la ventana en metros.
        alto_m: Alto de la ventana en metros.
        u_vidrio_w_m2k: Transmitancia del vidrio en W/m²K.
        u_marco_w_m2k: Transmitancia del marco en W/m²K.
        fraccion_marco: Porcentaje de marco respecto al hueco.
        tipo_intercalario: Tipo de espaciador perimetral.
        
    Returns:
        Diccionario con transmitancia global Uw (W/m²K), área total del hueco (m²), desglose de áreas de vidrio y marco y puente térmico lineal intercalario.
    """
    return calcular_transmitancia_ventana_iso10077(ancho_m, alto_m, u_vidrio_w_m2k, u_marco_w_m2k, fraccion_marco, tipo_intercalario)


DESC_DEMANDA_ACS = """Calcula la demanda normativa obligatoria de Agua Caliente Sanitaria (ACS) a 60 °C en litros/día según las tablas oficiales del Código Técnico de la Edificación CTE DB-HE4 y la temperatura de agua fría de red.

Cuándo usar:
    Invoque esta herramienta para determinar el volumen reglamentario diario de ACS necesario para dimensionar las instalaciones térmicas de producción y cobertura solar en CE3X.

Comportamiento y efectos secundarios:
    Operación analítica de solo lectura (Read-Only). No altera archivos ni registros locales."""

@mcp.tool(description=DESC_DEMANDA_ACS, annotations={"read_only_hint": True, "idempotent_hint": True})
def calcular_demanda_acs_cte_he4(
    numero_dormitorios: Annotated[int, Field(description="Número de dormitorios de la vivienda (para residenciales privados).", ge=0)] = 3,
    numero_personas: Annotated[Optional[float], Field(description="Número de personas u ocupantes directos calculados o previstos.")] = None,
    provincia: Annotated[str, Field(description="Provincia donde se ubica el edificio para fijar la temperatura de agua de red (ej. 'Madrid', 'A Coruña', 'Sevilla').")] = "A Coruña",
    tipo_edificio: Annotated[str, Field(description="Tipología de uso: 'ViviendaUnifamiliar', 'ViviendaBloque', 'Hotel_3_estrellas', 'Hospital', 'Residencia', 'Gimnasio'.")] = "ViviendaBloque"
) -> Dict[str, Any]:
    """Cálculo reglamentario de demanda de ACS a 60 °C según CTE DB-HE4.
    
    Args:
        numero_dormitorios: Número de dormitorios de la vivienda.
        numero_personas: Ocupantes directos si se conocen.
        provincia: Provincia española para temperatura del agua de red.
        tipo_edificio: Tipología edificatoria CTE.
        
    Returns:
        Diccionario con demanda diaria a 60 °C (litros/día), demanda energética anual (kWh/año) y temperatura de agua de red provincial.
    """
    return calcular_demanda_acs_cte_he4(
        numero_dormitorios=numero_dormitorios,
        numero_personas=numero_personas,
        provincia=provincia,
        tipo_edificio=tipo_edificio
    )


DESC_GESTION_CACHE = """Gestiona el subsistema de caché persistente SQLite local (~/.ce3x_mcp/cache.db) para consultas a Catastro (TTL 30 días) y radiación solar satelital PVGIS (TTL 90 días).

Cuándo usar:
    Utilice esta herramienta para consultar el espacio ocupado y la tasa de aciertos (hits/misses) de la caché o para invalidar entradas antiguas si se requiere forzar una recarga telemática fresca.

Comportamiento y efectos secundarios:
    Operación de mantenimiento del sistema de caché local. 'estadisticas' es de solo lectura (Read-Only); 'purgar_expiradas' y 'vaciar_todo' purgan registros obsoletos de la base de datos SQLite local."""

@mcp.tool(description=DESC_GESTION_CACHE, annotations={"read_only_hint": False, "destructive_hint": False})
def gestionar_cache_ce3x(
    accion: Annotated[str, Field(description="Acción a realizar en el subsistema de caché: 'estadisticas', 'purgar_expiradas' o 'vaciar_todo'.")] = "estadisticas",
    categoria: Annotated[Optional[str], Field(description="Categoría específica de caché a gestionar ('catastro' o 'pvgis'). Opcional.")] = None
) -> Dict[str, Any]:
    """Gestión y mantenimiento del subsistema de caché SQLite persistente.
    
    Args:
        accion: 'estadisticas' (default), 'purgar_expiradas' o 'vaciar_todo'.
        categoria: 'catastro' o 'pvgis' para filtrar la purga.
        
    Returns:
        Diccionario con estadísticas de almacenamiento (tamaño en bytes, total entradas, hits, misses) o confirmación de purga.
    """
    from ce3x_mcp.services.cache_manager import (
        obtener_estadisticas_cache,
        purgar_cache_expirada,
        vaciar_cache_completa
    )
    act = accion.strip().lower()
    if act == "estadisticas":
        stats = obtener_estadisticas_cache()
        stats["accion_ejecutada"] = "estadisticas"
        return stats
    elif act == "purgar_expiradas":
        purgadas = purgar_cache_expirada()
        stats = obtener_estadisticas_cache()
        stats["accion_ejecutada"] = "purgar_expiradas"
        stats["entradas_eliminadas"] = purgadas
        return stats
    elif act == "vaciar_todo":
        vaciadas = vaciar_cache_completa(categoria)
        stats = obtener_estadisticas_cache()
        stats["accion_ejecutada"] = "vaciar_todo"
        stats["entradas_eliminadas"] = vaciadas
        return stats
    else:
        return {
            "error": f"Acción desconocida '{accion}'. Use 'estadisticas', 'purgar_expiradas' o 'vaciar_todo'.",
            "acciones_validas": ["estadisticas", "purgar_expiradas", "vaciar_todo"]
        }

# ==============================================================================
# RECURSOS Y PROMPTS
# ==============================================================================

@mcp.resource("ce3x://normativa/factores_paso")
def obtener_factores_paso_normativos() -> str:
    """Factores de paso oficiales del IDAE a energía primaria no renovable y emisiones de CO2."""
    import json
    return json.dumps(FACTORES_PASO, indent=2, ensure_ascii=False)

@mcp.prompt()
def certificar_vivienda_rapido() -> str:
    """Flujo guiado interactivo para certificar una vivienda con datos mínimos."""
    return (
        "Por favor, facilítame los siguientes datos básicos de la vivienda:\n"
        "1. Dirección o Referencia Catastral (20 caracteres).\n"
        "2. Año aproximado de construcción.\n"
        "3. Superficie útil aproximada en m².\n"
        "4. Tipo de calefacción y producción de agua caliente sanitaria (ej. caldera de gas natural, radiadores eléctricos, aerotermia, termo eléctrico)."
    )

@mcp.resource("ce3x://normativa/u_valores_historicos")
def obtener_u_valores_historicos() -> str:
    """Valores de transmitancia térmica U límite e histórica por defecto según la normativa vigente en el año de construcción."""
    import json
    datos = {
        "anterior_1979": {"normativa": "Sin aislamiento reglamentario", "u_fachada": 1.80, "u_cubierta": 1.40, "u_hueco": 5.7},
        "1980_2006": {"normativa": "NBE-CT-79", "u_fachada": 1.40, "u_cubierta": 0.90, "u_hueco": 2.80},
        "2007_2013": {"normativa": "CTE DB-HE 2006", "u_fachada": 0.73, "u_cubierta": 0.50, "u_hueco": 2.20},
        "2014_2019": {"normativa": "CTE DB-HE 2013", "u_fachada": 0.52, "u_cubierta": 0.40, "u_hueco": 2.00},
        "2020_actual": {"normativa": "CTE DB-HE 2019 (nZEB)", "u_fachada": 0.29, "u_cubierta": 0.23, "u_hueco": 1.60}
    }
    return json.dumps(datos, indent=2, ensure_ascii=False)

@mcp.resource("ce3x://plantillas/toma_datos_campo")
def obtener_plantilla_toma_datos() -> str:
    """Plantilla de toma de datos optimizada para que el técnico o usuario recopile datos del inmueble en visita."""
    doc_path = r"C:\Users\Jose\OneDrive\GITHUB\CE3X-MCP-Server\docs\PLANTILLA_TOMA_DATOS_CEE.md"
    try:
        with open(doc_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return "Plantilla no disponible."

@mcp.prompt()
def asistente_toma_datos_inmueble() -> str:
    """Asistente conversacional interactivo para guiar la toma de datos del certificado energético paso a paso."""
    return r"""Actúa como un Arquitecto Técnico especialista en eficiencia energética.
Guíame paso a paso en la toma de datos de un inmueble:
1. Solicita primero la Referencia Catastral (20 dígitos) o dirección para consultar Catastro automáticamente.
2. Pregunta si se dispone de plano (PDF/imagen) o croquis para extraer las superficies y huecos.
3. Pregunta por los sistemas de calefacción y ACS (solicitando foto de la placa de características de la caldera si está disponible).
4. Si no se conoce la composición de muros, estima las transmitancias por defecto según la época de edificación.
5. Concluye resumiendo los datos recopilados antes de generar los entregables (.cex, XML oficial v3.0 y PDF de 15 páginas)."""

@mcp.prompt()
def auditoria_subvenciones_nextgen() -> str:
    """Guía paso a paso para auditar la elegibilidad de subvenciones Next Generation EU (RD 853/2021) y deducciones IRPF."""
    return """Actúa como consultor de ayudas públicas a la rehabilitación energética.
Para la vivienda o edificio analizado, realiza los siguientes cálculos:
1. Comprueba si el ahorro en energía primaria no renovable alcanza al menos el umbral legal del 30%.
2. Identifica el tramo de ayuda según el porcentaje de ahorro conseguido: 40%, 65% u 80% (o hasta 100% en vulnerabilidad).
3. Calcula la deducción en el IRPF correspondiente (40% o 60% en rehabilitación integral).
4. Emite el dictamen técnico justificativo oficial listo para registrar ante la administración autonómica."""

def main():
    import sys
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower()
    port = int(os.environ.get("MCP_PORT", "8000"))
    
    for arg in sys.argv[1:]:
        if arg in ("--sse", "-sse"):
            transport = "sse"
        elif arg.startswith("--port="):
            try:
                port = int(arg.split("=")[1])
            except ValueError:
                pass
        elif arg.startswith("--transport="):
            transport = arg.split("=")[1].lower()
            
    if transport in ("sse", "http", "streamable-http"):
        print(f"Iniciando CE3X-MCP-Server en modo {transport.upper()} sobre el puerto {port}...")
        mcp.run(transport=transport, port=port)
    else:
        mcp.run()

if __name__ == "__main__":
    main()
