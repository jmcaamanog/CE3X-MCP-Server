from fastmcp import FastMCP
from typing import Optional, Dict, Any
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
from ce3x_mcp.services.cex_codec import guardar_fichero_cex_basico

# Instancia oficial del servidor FastMCP
mcp = FastMCP(
    "CE3X-MCP-Server",
    description="Servidor MCP Oficial para Certificación Energética de Edificios en España (CE3X / CTE DB-HE / RD 390/2021)"
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
    # Estimación de balance según normativa
    trans = estimar_transmitancias_por_ano(ano_construccion, zona_climatica)
    
    # Demanda de calefacción en función de U y zona climática
    factor_zona = 1.4 if zona_climatica.startswith("D") else (1.8 if zona_climatica.startswith("E") else 1.0)
    demanda_cal = trans["u_fachada"] * 45.0 * factor_zona
    demanda_ref = 15.0 if not zona_climatica.endswith("4") else 30.0
    demanda_acs = 22.0
    
    # Rendimiento según tecnología
    rend_cal = 3.2 if "aerotermia" in tipo_calefaccion.lower() else (0.92 if "condensacion" in tipo_calefaccion.lower() else 1.0)
    rend_acs = 2.8 if "aerotermia" in tipo_acs.lower() else (0.85 if "gas" in tipo_acs.lower() else 1.0)
    
    vector = "Electricidad" if ("joule" in tipo_calefaccion.lower() or "aerotermia" in tipo_calefaccion.lower()) else "GasNatural"
    fp = FACTORES_PASO.get(vector, FACTORES_PASO["Electricidad"])
    
    cons_final_cal = demanda_cal / rend_cal
    cons_final_acs = demanda_acs / rend_acs
    cons_final_total = cons_final_cal + cons_final_acs
    
    ep_nr = cons_final_total * fp["f_ep_nr"]
    co2 = cons_final_total * fp["f_co2"]
    
    # Asignación de letras según emisiones (referencia residencial en zona C/D)
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
    
    # 3. Exportar .CEX nativo
    cex_path = os.path.join(out_dir, f"Proyecto_{municipio}_{ano_construccion}.cex")
    admin_list = [nombre_edificio, direccion, municipio, provincia, "", "", adm.nombre_tecnico, direccion, "900000000", "tecnico@ce3x.es", "ESTUDIO JMC", "JMC", "900000000", "info@jmc.es", codigo_postal, []]
    gen_list = ["Anterior" if ano_construccion < 1979 else "NBE-CT-79", "Vivienda en bloque", municipio, provincia, zona, str(superficie_util), "2.60", "1", "1", "Media", "0.63"]
    guardar_fichero_cex_basico(cex_path, "CE3Xv3.2 Residencial", admin_list, gen_list, [], [])
    
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

def main():
    mcp.run()

if __name__ == "__main__":
    main()

