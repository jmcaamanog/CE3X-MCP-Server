try:
    from fastmcp import FastMCP
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        class FastMCP:
            def __init__(self, name: str, description: str = ""):
                self.name = name
                self.description = description
                self.tools = {}
            def tool(self):
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
            def run(self):
                print(f"FastMCP {self.name} iniciado.")
from typing import Optional, Dict, Any, List
import os
import tempfile

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
from ce3x_mcp.services.cte_climate import (
    obtener_zona_climatica,
    estimar_transmitancias_por_ano,
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

# Instancia oficial del servidor FastMCP
mcp = FastMCP(
    "CE3X-MCP-Server",
    instructions="Servidor MCP Oficial para Certificación Energética de Edificios en España (CE3X / CTE DB-HE / RD 390/2021)"
)

@mcp.tool()
def consultar_catastro(referencia_catastral: str) -> Dict[str, Any]:
    """
    Consulta telemática a la Sede Electrónica del Catastro de España para obtener
    dirección oficial, municipio, provincia y código postal a partir de la Referencia Catastral.
    """
    return consultar_catastro_por_rc(referencia_catastral)

@mcp.tool()
def determinar_zona_climatica(provincia: str, municipio: str, altitud_m: float = 0.0) -> Dict[str, str]:
    """
    Determina la zona climática CTE DB-HE (ej. C1, D3, A3, E1) en función de la provincia,
    municipio y altitud sobre el nivel del mar.
    """
    zona = obtener_zona_climatica(provincia, municipio, altitud_m)
    return {
        "provincia": provincia,
        "municipio": municipio,
        "altitud_m": str(altitud_m),
        "zona_climatica_cte": zona
    }

@mcp.tool()
def estimar_envolvente_por_defecto(ano_construccion: int, zona_climatica: str = "C1") -> Dict[str, Any]:
    """
    Estima las transmitancias térmicas (U en W/m²K) de fachadas, cubiertas y huecos
    según el año de construcción del edificio conforme a los manuales de fundamentos técnicos de CE3X.
    """
    return estimar_transmitancias_por_ano(ano_construccion, zona_climatica)

@mcp.tool()
def calcular_calificacion_energetica(
    superficie_util: float,
    ano_construccion: int,
    zona_climatica: str = "C1",
    tipo_calefaccion: str = "EfectoJoule",
    tipo_acs: str = "EfectoJoule"
) -> Dict[str, Any]:
    """
    Calcula la demanda energética estimada, consumo de energía primaria no renovable,
    emisiones de CO2 y asigna las letras de calificación energética (A a G).
    """
    trans = estimar_transmitancias_por_ano(ano_construccion, zona_climatica)
    
    factor_zona = 1.4 if zona_climatica.startswith("D") else (1.8 if zona_climatica.startswith("E") else 1.0)
    demanda_cal = trans["u_fachada"] * 45.0 * factor_zona
    demanda_ref = 15.0 if not zona_climatica.endswith("4") else 30.0
    demanda_acs = 22.0
    
    rend_cal = 3.2 if "aerotermia" in tipo_calefaccion.lower() else (0.92 if "condensacion" in tipo_calefaccion.lower() else 1.0)
    rend_acs = 2.8 if "aerotermia" in tipo_acs.lower() else (0.85 if "gas" in tipo_acs.lower() else 1.0)
    
    vector = "Electricidad" if ("joule" in tipo_calefaccion.lower() or "aerotermia" in tipo_calefaccion.lower()) else "GasNatural"
    fp = FACTORES_PASO.get(vector, FACTORES_PASO["Electricidad"])
    
    cons_final_cal = demanda_cal / rend_cal
    cons_final_acs = demanda_acs / rend_acs
    cons_final_total = cons_final_cal + cons_final_acs
    
    ep_nr = cons_final_total * fp["f_ep_nr"]
    co2 = cons_final_total * fp["f_co2"]
    
    if co2 < 8.0:
        letra = "A"
    elif co2 < 14.0:
        letra = "B"
    elif co2 < 24.0:
        letra = "C"
    elif co2 < 38.0:
        letra = "D"
    elif co2 < 60.0:
        letra = "E"
    elif co2 < 75.0:
        letra = "F"
    else:
        letra = "G"
        
    return {
        "demanda_calefaccion_kwh_m2a": round(demanda_cal, 2),
        "demanda_refrigeracion_kwh_m2a": round(demanda_ref, 2),
        "demanda_acs_kwh_m2a": round(demanda_acs, 2),
        "consumo_energia_primaria_nr_kwh_m2a": round(ep_nr, 2),
        "emisiones_co2_kg_m2a": round(co2, 2),
        "calificacion_global_emisiones": letra,
        "calificacion_global_energia_primaria": letra,
        "vector_energetico_principal": vector
    }

@mcp.tool()
def analizar_modelo_bim_ifc(ifc_path: str) -> Dict[str, Any]:
    """
    Abre y analiza un modelo BIM IFC (IFC2X3 o IFC4) mediante IfcOpenShell, extrayendo
    las superficies útiles de estancias (IfcSpace), muros de fachada exterior (IfcWall)
    y carpinterías exteriores (IfcWindow/IfcDoor) para su integración en CE3X.
    """
    return extraer_envolvente_desde_ifc(ifc_path)

@mcp.tool()
def analizar_plano_arquitectura_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Abre y analiza un plano arquitectónico en PDF mediante PyMuPDF, extrayendo
    superficies útiles de estancias (m²) y cuadros de carpintería de huecos y ventanas.
    """
    return analizar_plano_distribucion_pdf(pdf_path)

@mcp.tool()
def analizar_ficha_equipo_clima(descripcion_o_ficha: str) -> Dict[str, Any]:
    """
    Analiza la descripción o texto de la ficha técnica de un equipo térmico
    (aerotermia, caldera de condensación, bomba de calor, termo) y extrae su potencia,
    rendimiento estacional (SCOP/COP/SEER) y vector energético para CE3X.
    """
    return analizar_datos_equipo_climatizacion(descripcion_o_ficha)

@mcp.tool()
def calcular_produccion_fotovoltaica_pvgis(
    latitud: float,
    longitud: float,
    potencia_pico_kw: float = 3.0,
    inclinacion_grados: float = 35.0,
    azimut_grados: float = 0.0
) -> Dict[str, Any]:
    """
    Calcula con precisión científica la producción de energía solar fotovoltaica (kWh/año y mensual)
    conectando con la API oficial PVGIS de la Comisión Europea (JRC) con radiación satelital SARAH-2.
    """
    return calcular_produccion_solar_pvgis(latitud, longitud, potencia_pico_kw, inclinacion_grados, azimut_grados)

@mcp.tool()
def proponer_medidas_mejora_rd390(
    superficie_util: float,
    ano_construccion: int,
    zona_climatica: str = "C1",
    tipo_calefaccion: str = "EfectoJoule",
    tipo_acs: str = "EfectoJoule"
) -> Dict[str, Any]:
    """
    Genera automáticamente los 3 paquetes de medidas de mejora exigidos por el Real Decreto 390/2021
    (Envolvente SATE + Carpinterías, Aerotermia y Solución Integral con Fotovoltaica),
    calculando la inversión estimada (€), el ahorro en factura (€/año), la nueva letra energética y el retorno (payback).
    """
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
    medidas = calcular_paquetes_medidas_mejora(proyecto, res)
    return {
        "calificacion_actual": calc,
        "medidas_de_mejora": [m.model_dump() for m in medidas]
    }

@mcp.tool()
def emitir_dictamen_subvenciones_nextgen(
    superficie_util: float,
    ano_construccion: int,
    zona_climatica: str = "C1",
    tipo_calefaccion: str = "EfectoJoule",
    tipo_acs: str = "EfectoJoule",
    paquete_mejora: int = 3
) -> Dict[str, Any]:
    """
    Genera el informe técnico justificativo y dictamen oficial de cumplimiento para las
    ayudas Next Generation EU (Real Decreto 853/2021) y deducciones del IRPF (D.A. 50ª Ley IRPF),
    acreditando si se supera el umbral del 30% de reducción en energía primaria no renovable.
    - paquete_mejora: 1 (Envolvente), 2 (Aerotermia) o 3 (Integral con Solar FV).
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
    
    idx = max(0, min(paquete_mejora - 1, len(medidas) - 1))
    medida_sel = medidas[idx]
    
    return generar_informe_justificativo_nextgen(proyecto, res, medida_sel)

@mcp.tool()
def generar_certificado_completo(
    nombre_edificio: str,
    direccion: str,
    municipio: str,
    provincia: str,
    codigo_postal: str,
    superficie_util: float,
    ano_construccion: int,
    tipo_calefaccion: str = "EfectoJoule",
    tipo_acs: str = "EfectoJoule",
    referencia_catastral: Optional[str] = None,
    directorio_salida: Optional[str] = None
) -> Dict[str, Any]:
    """
    Genera el conjunto completo de entregables oficiales para el certificado energético:
    1. Archivo XML oficial (DatosEnergeticosDelEdificio v3.0) para registro telemático.
    2. Archivo PDF oficial compilado con Typst / xml2cert.
    3. Archivo de proyecto editable .cex para CE3X.
    """
    out_dir = directorio_salida or os.path.join(tempfile.gettempdir(), "ce3x_certificados")
    os.makedirs(out_dir, exist_ok=True)
    
    zona = obtener_zona_climatica(provincia, municipio)
    calc = calcular_calificacion_energetica(
        superficie_util=superficie_util,
        ano_construccion=ano_construccion,
        zona_climatica=zona,
        tipo_calefaccion=tipo_calefaccion,
        tipo_acs=tipo_acs
    )
    
    adm = DatosAdministrativos(
        nombre_edificio=nombre_edificio,
        direccion=direccion,
        municipio=municipio,
        provincia=provincia,
        codigo_postal=codigo_postal,
        referencia_catastral=referencia_catastral
    )
    
    gen = DatosGenerales(
        ano_construccion=ano_construccion,
        zona_climatica=zona,
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
    
    # 1. Generar XML Oficial
    xml_content = generar_xml_oficial_30(proyecto, res)
    xml_path = os.path.join(out_dir, f"Certificado_{municipio}_{ano_construccion}.xml")
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_content)
        
    # 2. Compilar PDF Oficial
    pdf_ok, pdf_res = compilar_pdf_desde_xml(xml_path, out_dir)
    
    # 3. Exportar .CEX nativo completo y compatible con la interfaz CE3X
    cex_path = os.path.join(out_dir, f"Proyecto_{municipio}_{ano_construccion}.cex")
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
        nombre_tecnico="Técnico Certificador Colegiado",
        nif_tecnico="00000000T",
        titulacion="Arquitectura técnica o aparejadores"
    )
    
    return {
        "estado": "completado",
        "calificacion_obtenida": calc["calificacion_global_emisiones"],
        "archivo_xml_oficial": xml_path,
        "archivo_pdf_oficial": pdf_res if pdf_ok else f"No se pudo compilar PDF: {pdf_res}",
        "archivo_cex_ce3x": cex_path,
        "resumen_energetico": calc
    }

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
    return """Actúa como un Arquitecto Técnico especialista en eficiencia energética.
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
    mcp.run()

if __name__ == "__main__":
    main()



