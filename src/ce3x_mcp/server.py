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

# Instancia oficial del servidor FastMCP
mcp = FastMCP(
    "CE3X-MCP-Server",
    instructions=(
        "Servidor MCP Oficial para Certificación Energética de Edificios en España (CE3X v3.2 / CTE DB-HE / RD 390/2021).\n\n"
        "PROTOCOLO DE INTERACCIÓN OBLIGATORIO PARA LA IA:\n"
        "1. PRIMER CONTACTO: Al iniciar la conversación o cuando el usuario pida certificar un inmueble, "
        "lo PRIMERO que debes preguntarle con cortesía es:\n"
        "   '¿En qué carpeta de tu ordenador tienes los archivos o toma de datos de la visita? "
        "(Por favor, indícame la ruta completa, por ejemplo: C:\\MisVisitas\\Piso_RuaReal)'.\n"
        "2. ESTRUCTURACIÓN AUTOMÁTICA:\n"
        "   Una vez recibida la ruta, ejecuta 'organizar_carpeta_visita'. Si los archivos están sueltos o desordenados, "
        "la herramienta los organizará automáticamente en las 5 carpetas estándar:\n"
        "   - INFORMACION/ (apuntes, notas, datos de Catastro)\n"
        "   - PLANOS/ (planos PDF, croquis acotados, IFC)\n"
        "   - FOTOS/ (fotos generales de fachadas, ventanas, sombras)\n"
        "   - INSTALACIONES/ (fotos de placas de calderas, termos, bombas de calor y fichas técnicas)\n"
        "   - CERTIFICADO/ (entregables oficiales finales)\n"
        "   Informa al usuario de cómo ha quedado ordenada su carpeta para que le conste en adelante.\n"
        "3. AUDITORÍA Y PREGUNTAS QUIRÚRGICAS:\n"
        "   Ejecuta 'auditar_carpeta_visita', analiza los datos recopilados y formula ÚNICAMENTE 1 o 2 preguntas "
        "quirúrgicas si falta algún dato no deducible (orientación o sombras).\n"
        "4. GENERACIÓN AUTOMÁTICA EN 'CERTIFICADO/':\n"
        "   Ejecuta 'certificar_desde_carpeta_visita'. Todos los entregables (.cex, XML oficial v3.0, PDF de 15 págs., "
        "informe de mejoras y dictamen NextGen en PDF/MD) quedarán generados directamente en la subcarpeta CERTIFICADO/."
    )
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
        referencia_catastral=referencia_catastral or "",
        nombre_tecnico="Tecnico Certificador Colegiado",
        nif_tecnico="00000000T",
        titulacion="Arquitectura tecnica o aparejadores"
    )
    
    return {
        "estado": "completado",
        "calificacion_obtenida": calc["calificacion_global_emisiones"],
        "archivo_xml_oficial": xml_path,
        "archivo_pdf_oficial": pdf_res if pdf_ok else f"No se pudo compilar PDF: {pdf_res}",
        "archivo_cex_ce3x": cex_path,
        "resumen_energetico": calc
    }


@mcp.tool()
def organizar_carpeta_visita(ruta_carpeta: str) -> Dict[str, Any]:
    """
    Crea la estructura estándar de 5 carpetas y clasifica automáticamente los archivos:
    - INFORMACION/   -> Notas de visita, Referencia Catastral, apuntes y datos.
    - PLANOS/        -> Planos de distribución en PDF, croquis acotados, modelos BIM (IFC/DWG).
    - FOTOS/         -> Fotografías del inmueble (fachada exterior, huecos y carpinterías).
    - INSTALACIONES/ -> Fotos de placas de calderas, termos, bombas de calor y fichas técnicas.
    - CERTIFICADO/   -> Carpeta oficial de salida para .cex, .xml, .pdf y mejoras NextGen.

    Si la carpeta del inmueble contiene archivos sueltos en su raíz o en carpetas no estándar,
    los clasifica y mueve automáticamente a su subcarpeta correspondiente, generando además
    la ficha 'LEEME_ESTRUCTURA_VISITA.txt'.
    """
    return organizar_carpeta_visita_impl(ruta_carpeta)

@mcp.tool()
def auditar_carpeta_visita(ruta_carpeta: str) -> Dict[str, Any]:
    """
    Audita de forma autónoma una carpeta de visita técnica (croquis, notas, planos PDF,
    imágenes, modelos BIM), extrae datos catastrales y arquitectónicos, deduce la envolvente
    según normativa histórica y genera las preguntas quirúrgicas para el técnico antes de certificar.
    Define automáticamente la subcarpeta 'CERTIFICADO/' para la entrega final.
    """
    return auditar_carpeta_inmueble(ruta_carpeta)

@mcp.tool()
def certificar_desde_carpeta_visita(
    ruta_carpeta: str,
    orientacion_principal: str = "Sur",
    tipo_calefaccion: Optional[str] = None,
    tipo_acs: Optional[str] = None,
    nombre_edificio: Optional[str] = None
) -> Dict[str, Any]:
    """
    Certifica de forma automática el inmueble a partir de la carpeta de visita.
    Crea la subcarpeta 'CERTIFICADO/' dentro de la carpeta del inmueble y genera directamente:
    1. Proyecto nativo editable para CE3X (.cex).
    2. Archivo XML oficial v3.0 para registro telemático (.xml).
    3. Informe oficial de 15 páginas compilado con Typst (.pdf).
    4. Informe de Medidas de Mejora RD 390/2021 y Dictamen NextGen (.md / .pdf).
    """
    return certificar_inmueble_desde_carpeta(
        ruta_carpeta=ruta_carpeta,
        orientacion_principal=orientacion_principal,
        tipo_calefaccion=tipo_calefaccion,
        tipo_acs=tipo_acs,
        nombre_edificio=nombre_edificio
    )

@mcp.tool()
def registrar_visita_presencial(
    fecha_visita: str,
    pruebas_realizadas: Optional[List[str]] = None,
    observaciones_tecnicas: Optional[str] = None
) -> Dict[str, Any]:
    """
    Registra formalmente la visita presencial obligatoria exigida por el Art. 8 del RD 390/2021
    y genera el bloque documental oficial para el Anexo IV del Certificado de Eficiencia Energética.
    Pruebas disponibles: inspeccion_visual, medicion_laser, comprobacion_placas, termografia,
    ensayo_blower_door, facturas_electricas.
    """
    return registrar_visita_e_inspeccion(
        fecha_visita=fecha_visita,
        pruebas_realizadas=pruebas_realizadas,
        observaciones_tecnicas=observaciones_tecnicas
    )

@mcp.tool()
def registrar_ensayo_estanqueidad_blower_door(
    volumen_neto_m3: float,
    superficie_envolvente_m2: float,
    caudal_50pa_m3h: float
) -> Dict[str, Any]:
    """
    Procesa un ensayo de estanqueidad al aire según norma UNE-EN ISO 9972 (Blower Door).
    Calcula el valor n50 (ren/h a 50 Pa), q50 (m3/h·m2), la tasa de infiltración equivalente
    para el motor CE3X y emite el diagnóstico de hermeticidad (Passivhaus / CTE DB-HE 2019).
    """
    return registrar_ensayo_blower_door(
        volumen_neto_m3=volumen_neto_m3,
        superficie_envolvente_m2=superficie_envolvente_m2,
        caudal_50pa_m3h=caudal_50pa_m3h
    )

@mcp.tool()
def calcular_puentes_termicos(
    ano_construccion: int,
    perimetro_forjado_m: float,
    perimetro_huecos_m: float,
    longitud_pilares_m: float = 0.0
) -> Dict[str, Any]:
    """
    Calcula las transmitancias térmicas lineales (psi en W/m·K) y la pérdida térmica global (W/K)
    asociada a puentes térmicos en frentes de forjado, jambas, dinteles, alféizares y pilares
    según el catálogo oficial del Documento de Apoyo CTE (DA DB-HE / 3).
    """
    return calcular_puentes_termicos_cte(
        ano_construccion=ano_construccion,
        perimetro_forjado_m=perimetro_forjado_m,
        perimetro_huecos_m=perimetro_huecos_m,
        longitud_pilares_m=longitud_pilares_m
    )

@mcp.tool()
def configurar_perfil_tecnico_colegiado(
    nombre_tecnico: str,
    nif_tecnico: str,
    titulacion: str = "Arquitecto Técnico",
    colegio_profesional: Optional[str] = None,
    numero_colegiado: Optional[str] = None,
    razon_social: Optional[str] = None,
    comunidad_autonoma: str = "Galicia"
) -> Dict[str, Any]:
    """
    Configura y guarda de forma persistente los datos colegiales del técnico certificador.
    Se inyectarán automáticamente en todos los proyectos .cex, archivos XML oficiales v3.0
    y documentos PDF generados.
    """
    return guardar_perfil_tecnico(
        nombre_tecnico=nombre_tecnico,
        nif_tecnico=nif_tecnico,
        titulacion=titulacion,
        colegio_profesional=colegio_profesional,
        numero_colegiado=numero_colegiado,
        razon_social=razon_social,
        comunidad_autonoma=comunidad_autonoma
    )

@mcp.tool()
def calcular_sombras_hueco(
    orientacion: str = "Sur",
    ancho_hueco_m: float = 1.20,
    alto_hueco_m: float = 1.20,
    retranqueo_m: float = 0.0,
    vuelo_voladizo_m: float = 0.0,
    tiene_toldo: bool = False
) -> Dict[str, Any]:
    """
    Calcula los factores de sombra estacionales (verano e invierno) y el factor solar modificado
    de un hueco por voladizo, retranqueo o toldo, conforme al CTE DB-HE y CE3X.
    """
    return calcular_sombras_estacionales_hueco(
        orientacion=orientacion,
        ancho_hueco_m=ancho_hueco_m,
        alto_hueco_m=alto_hueco_m,
        retranqueo_m=retranqueo_m,
        vuelo_voladizo_m=vuelo_voladizo_m,
        tiene_toldo=tiene_toldo
    )

@mcp.tool()
def contrastar_consumo_facturas_reales(
    consumo_teorico_kwh_ano: float,
    electricidad_real_kwh: float,
    gas_natural_real_kwh: float = 0.0,
    gasoleo_real_litros: float = 0.0
) -> Dict[str, Any]:
    """
    Compara el consumo real de energía de los últimos 12 meses (electricidad, gas natural o gasóleo)
    frente a la demanda teórica calculada en el modelo de CE3X, detectando desviaciones de uso
    y hábitos de confort del usuario.
    """
    return contrastar_facturas_reales(
        consumo_teorico_kwh_ano=consumo_teorico_kwh_ano,
        electricidad_real_kwh=electricidad_real_kwh,
        gas_natural_real_kwh=gas_natural_real_kwh,
        gasoleo_real_litros=gasoleo_real_litros
    )

@mcp.resource("ce3x://librerias/catalogo_soluciones_constructivas")
def obtener_catalogo_soluciones_constructivas() -> str:
    """Catálogo oficial de arquetipos constructivos de muros, vidrios y carpinterías según IDAE y CE3X."""
    import json
    catalogo = {
        "muros_fachada": CATALOGO_MUROS_FACHADA,
        "vidrios": CATALOGO_VIDRIOS,
        "marcos_carpinteria": CATALOGO_MARCOS_CARPINTERIA
    }
    return json.dumps(catalogo, indent=2, ensure_ascii=False)

@mcp.prompt()
def iniciar_asistente_visita() -> str:
    """Prompt inicial de bienvenida para solicitar la carpeta de visita y organizar los archivos."""
    return """Actúa como un Arquitecto Técnico experto en certificación energética con CE3X.
Al iniciar la interacción con el usuario:
1. Pregúntale amablemente: '¿En qué carpeta de tu ordenador tienes los archivos o toma de datos de la visita del inmueble? (Por favor, facilítame la ruta completa, por ejemplo: C:\MisVisitas\Piso_RuaReal)'.
2. Indícale que si tiene los archivos sueltos (fotos, planos, notas), los organizarás automáticamente en las 5 carpetas estándar:
   - INFORMACION/ (apuntes, notas, datos del cliente)
   - PLANOS/ (planos en PDF, croquis acotados, modelos IFC/DWG)
   - FOTOS/ (fotos generales del inmueble, fachadas y huecos)
   - INSTALACIONES/ (fotos de placas de calderas, termos, bombas de calor y fichas técnicas)
   - CERTIFICADO/ (entregables oficiales finales: .cex, .xml, .pdf del informe y mejoras NextGen)
3. En cuanto el usuario te proporcione la ruta, ejecuta 'organizar_carpeta_visita' y luego 'auditar_carpeta_visita'."""

@mcp.prompt()
def asistente_auditoria_carpeta_visita(ruta_carpeta: str = "ruta/a/carpeta_inmueble") -> str:
    """Asistente para auditar una carpeta de visita y realizar la entrevista interactiva al técnico."""
    return (
        f"Por favor, analiza la carpeta de visita '{ruta_carpeta}'. "
        "Ejecuta la herramienta 'auditar_carpeta_visita' para identificar qué documentos "
        "y datos catastrales o de planos están presentes. Presenta un resumen conciso "
        "y hazme únicamente las preguntas sobre los datos críticos que falten (sombras, color de marcos, instalaciones) "
        "antes de generar el certificado completo."
    )



@mcp.tool()
def calcular_sombras_obstaculo_edificio_enfrente(
    distancia_edificio_m: float,
    altura_edificio_m: float,
    orientacion_fachada: str = "Sur",
    descripcion_obstaculo: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calcula el angulo de elevacion alfa del patron de sombra producido por un obstaculo remoto
    (edificio de enfrente, colindante o accidente geografico) y su factor reductor de radiacion
    solar estacional F_sh conforme al CTE DB-HE y el motor de calculo oficial de CE3X v3.2.
    """
    return calcular_patron_sombras_edificio_colindante(
        distancia_edificio_m=distancia_edificio_m,
        altura_edificio_m=altura_edificio_m,
        orientacion_fachada=orientacion_fachada,
        descripcion_obstaculo=descripcion_obstaculo
    )

@mcp.tool()
def calcular_parametros_terciario_local_comercial(
    tipo_actividad: str = "Comercio",
    superficie_util_m2: float = 100.0,
    tipo_luminaria: str = "LED",
    nivel_iluminacion_lux: Optional[float] = None
) -> Dict[str, Any]:
    """
    Estima los parametros normativos obligatorios de CE3X para edificios de uso Terciario y Locales
    Comerciales: potencia de iluminacion instalada (W/m2), VEEI segun CTE DB-HE 3, consumo anual estimado
    y tasa de renovacion de aire exterior / calidad del aire segun RITE (IDA 2 / IDA 3).
    """
    return estimar_parametros_terciario_comercial(
        tipo_actividad=tipo_actividad,
        superficie_util_m2=superficie_util_m2,
        tipo_luminaria=tipo_luminaria,
        nivel_iluminacion_lux=nivel_iluminacion_lux
    )



@mcp.tool()
def registrar_ensayo_flujometria_termica_in_situ(
    flujo_medio_w_m2: float,
    temp_interior_media_c: float,
    temp_exterior_media_c: float,
    duracion_ensayo_horas: float = 72.0,
    elemento_analizado: str = "Fachada principal"
) -> Dict[str, Any]:
    """
    Registra formalmente un ensayo in situ de flujometria termica con termoflujometro y sondas de
    contacto conforme a la norma UNE-EN ISO 9869-1, calculando la transmitancia termica U real
    (W/m2K) del cerramiento para justificar el nivel conocido en CE3X y el Anexo IV del RD 390/2021.
    """
    return registrar_ensayo_flujometria_termica_iso9869(
        flujo_medio_w_m2=flujo_medio_w_m2,
        temp_interior_media_c=temp_interior_media_c,
        temp_exterior_media_c=temp_exterior_media_c,
        duracion_ensayo_horas=duracion_ensayo_horas,
        elemento_analizado=elemento_analizado
    )



@mcp.tool()
def calcular_transmitancia_ventana_iso10077(
    ancho_m: float,
    alto_m: float,
    u_vidrio_w_m2k: float,
    u_marco_w_m2k: float,
    fraccion_marco: float = 0.25,
    tipo_intercalario: str = "termicamente_mejorado"
) -> Dict[str, Any]:
    """
    Calcula la transmitancia termica total Uw (W/m2K) de una ventana conforme a la norma
    UNE-EN ISO 10077-1 (metodo de componentes: vidrio Ug, marco Uf y puente termico de intercalario
    Psi_g) para justificar el nivel conocido de huecos en el software oficial CE3X v3.2.
    """
    return calcular_transmitancia_ventana_iso10077(
        ancho_m=ancho_m,
        alto_m=alto_m,
        u_vidrio_w_m2k=u_vidrio_w_m2k,
        u_marco_w_m2k=u_marco_w_m2k,
        fraccion_marco=fraccion_marco,
        tipo_intercalario=tipo_intercalario
    )

@mcp.tool()
def calcular_demanda_acs_cte_he4(
    numero_dormitorios: int = 3,
    numero_personas: Optional[float] = None,
    provincia: str = "A Coruña",
    tipo_edificio: str = "ViviendaBloque"
) -> Dict[str, Any]:
    """
    Calcula la demanda normativa obligatoria de Agua Caliente Sanitaria (ACS) a 60 C en litros/dia
    y la demanda energetica anual en kWh/ano conforme a la Tabla 3.1 del CTE DB-HE 4 y la temperatura
    media provincial del agua de red para introducir en los Datos Generales de CE3X.
    """
    return calcular_demanda_acs_cte_he4(
        numero_dormitorios=numero_dormitorios,
        numero_personas=numero_personas,
        provincia=provincia,
        tipo_edificio=tipo_edificio
    )

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



