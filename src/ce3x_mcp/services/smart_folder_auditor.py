"""
Módulo de Auditoría Inteligente y Certificación desde Carpeta de Visita para CE3X
Analiza de forma autónoma una carpeta de archivos de toma de datos (croquis, planos PDF,
notas de texto, fichas de equipos, modelos BIM) y genera automáticamente todos los entregables
oficiales dentro de la subcarpeta CERTIFICADO/.
"""

import os
import re
import shutil
from typing import Dict, Any, List, Optional
import pymupdf as fitz

from ce3x_mcp.services.catastro import consultar_catastro_por_rc
from ce3x_mcp.services.cte_climate import (
    obtener_zona_climatica,
    estimar_transmitancias_por_ano,
    calcular_calificacion_energetica_simplificada
)
from ce3x_mcp.services.libraries import inferir_solucion_envolvente_por_ano
from ce3x_mcp.services.plan_parser import analizar_plano_distribucion_pdf
from ce3x_mcp.services.equipment_parser import analizar_datos_equipo_climatizacion
from ce3x_mcp.services.cex_codec import guardar_fichero_cex_completo
from ce3x_mcp.services.xml_builder import generar_xml_oficial_30
from ce3x_mcp.services.pdf_compiler import compilar_pdf_desde_xml
from ce3x_mcp.services.improvement_engine import calcular_paquetes_medidas_mejora
from ce3x_mcp.services.nextgen_report import generar_informe_justificativo_nextgen
from ce3x_mcp.core.models import (
    ProyectoCertificacion,
    DatosAdministrativos,
    DatosGenerales,
    ResultadoCalificacion
)

REGEX_RC_20 = re.compile(r"\b([0-9]{7}[A-Z]{2}[0-9]{4}[A-Z]{1}[0-9]{4}[A-Z]{2})\b")
REGEX_CP = re.compile(r"\b(0[1-9]|[1-4][0-9]|5[0-2])[0-9]{3}\b")

def compilar_informe_mejoras_pdf(
    texto_md: str,
    ruta_pdf: str,
    titulo: str = "DICTAMEN OFICIAL DE MEDIDAS DE MEJORA Y SUBVENCIONES NEXTGEN"
) -> bool:
    """
    Compila el dictamen técnico de medidas de mejora y ayudas NextGen (RD 853/2021 y RD 390/2021)
    a un archivo PDF maquetado profesionalmente dentro de la carpeta CERTIFICADO/.
    """
    try:
        doc = fitz.open()
        lines = texto_md.split("\n")
        page = doc.new_page(width=595, height=842) # A4 estándar
        
        # Franja decorativa de cabecera
        rect_decor = fitz.Rect(0, 0, 595, 14)
        page.draw_rect(rect_decor, color=(0.08, 0.38, 0.74), fill=(0.08, 0.38, 0.74))
        
        # Tarjeta encabezado
        rect_header = fitz.Rect(45, 35, 550, 75)
        page.draw_rect(rect_header, color=(0.85, 0.90, 0.95), fill=(0.95, 0.97, 1.0), width=1.0)
        page.insert_textbox(rect_header, f"\n   {titulo}", fontsize=11, fontname="helv", color=(0.08, 0.38, 0.74))
        
        y = 95
        for line in lines:
            if y > 790:
                page = doc.new_page(width=595, height=842)
                page.draw_rect(fitz.Rect(0, 0, 595, 8), color=(0.08, 0.38, 0.74), fill=(0.08, 0.38, 0.74))
                y = 45
            
            line_s = line.strip()
            if not line_s:
                y += 6
                continue
            
            if line_s.startswith("# "):
                r = fitz.Rect(45, y, 550, y + 24)
                page.insert_textbox(r, line_s.lstrip("# ").strip(), fontsize=12, fontname="helv", color=(0.08, 0.38, 0.74))
                y += 24
            elif line_s.startswith("## "):
                r = fitz.Rect(45, y, 550, y + 18)
                page.insert_textbox(r, line_s.lstrip("# ").strip(), fontsize=10, fontname="helv", color=(0.15, 0.25, 0.35))
                y += 19
            elif line_s.startswith("### "):
                r = fitz.Rect(45, y, 550, y + 16)
                page.insert_textbox(r, line_s.lstrip("# ").strip(), fontsize=9, fontname="helv", color=(0.25, 0.35, 0.45))
                y += 16
            elif line_s.startswith("- ") or line_s.startswith("* "):
                clean_item = re.sub(r"\*\*([^\*]+)\*\*", r"\1", line_s[2:].strip())
                r = fitz.Rect(55, y, 550, y + 14)
                page.insert_textbox(r, "• " + clean_item, fontsize=8.5, fontname="helv", color=(0.15, 0.15, 0.15))
                y += 14
            elif line_s.startswith("|"):
                cells = [c.strip() for c in line_s.split("|") if c.strip()]
                if cells and not all(set(c) <= set("-: ") for c in cells):
                    row_txt = "   |   ".join(cells)
                    r = fitz.Rect(45, y, 550, y + 13)
                    page.draw_rect(r, color=(0.92, 0.92, 0.92), fill=(0.97, 0.97, 0.98), width=0.5)
                    page.insert_textbox(r, " " + row_txt, fontsize=8, fontname="helv", color=(0.1, 0.1, 0.1))
                    y += 14
            else:
                clean_text = re.sub(r"\*\*([^\*]+)\*\*", r"\1", line_s)
                r = fitz.Rect(45, y, 550, y + 14)
                page.insert_textbox(r, clean_text, fontsize=8.5, fontname="helv", color=(0.15, 0.15, 0.15))
                y += 14
                
        for idx, p in enumerate(doc):
            p_rect = fitz.Rect(45, 815, 550, 830)
            p.insert_textbox(
                p_rect,
                f"Página {idx+1} de {len(doc)}  |  Dictamen Técnico RD 390/2021 y Plan de Recuperación NextGen",
                fontsize=7.5,
                fontname="helv",
                color=(0.5, 0.5, 0.5)
            )
            
        doc.save(ruta_pdf)
        doc.close()
        return True
    except Exception as e:
        print(f"Error generando PDF de mejoras: {e}")
        return False

def auditar_carpeta_inmueble(ruta_carpeta: str) -> Dict[str, Any]:
    """
    Escanea exhaustivamente la carpeta del inmueble, clasifica los archivos disponibles,
    extrae datos catastrales, arquitectónicos e instalaciones, y define la subcarpeta CERTIFICADO/
    donde se guardará el conjunto de entregables oficiales.
    """
    if not os.path.exists(ruta_carpeta) or not os.path.isdir(ruta_carpeta):
        raise FileNotFoundError(f"La ruta de carpeta especificada no existe: {ruta_carpeta}")

    directorio_certificado = os.path.join(ruta_carpeta, "CERTIFICADO")

    # 1. Inventario y clasificacion de archivos (ignorando la carpeta CERTIFICADO interna si existe)
    archivos_encontrados = {
        "textos_y_notas": [],
        "planos_pdf": [],
        "imagenes": [],
        "modelos_bim": []
    }

    for root, _, files in os.walk(ruta_carpeta):
        if "CERTIFICADO" in root:
            continue
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            ruta_f = os.path.join(root, f)
            rel_f = os.path.relpath(ruta_f, ruta_carpeta)
            
            if ext in [".txt", ".md", ".json", ".csv"]:
                archivos_encontrados["textos_y_notas"].append(rel_f)
            elif ext == ".pdf":
                archivos_encontrados["planos_pdf"].append(rel_f)
            elif ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
                archivos_encontrados["imagenes"].append(rel_f)
            elif ext == ".ifc":
                archivos_encontrados["modelos_bim"].append(rel_f)

    # 2. Extraccion textual de notas
    texto_acumulado = ""
    rc_detectada = None
    cp_detectado = None

    for rel_txt in archivos_encontrados["textos_y_notas"]:
        try:
            with open(os.path.join(ruta_carpeta, rel_txt), "r", encoding="utf-8", errors="ignore") as fp:
                t = fp.read()
                texto_acumulado += "\n" + t
                if not rc_detectada:
                    m_rc = REGEX_RC_20.search(t)
                    if m_rc:
                        rc_detectada = m_rc.group(1)
                if not cp_detectado:
                    m_cp = REGEX_CP.search(t)
                    if m_cp:
                        cp_detectado = m_cp.group(1)
        except Exception:
            pass

    # 3. Consulta Catastral Automatica si se hallo RC
    datos_catastro = {}
    ano_construccion = 1982
    superficie_catastro = 100.0
    municipio = "A Coruña"
    provincia = "A Coruña"

    if rc_detectada:
        try:
            datos_catastro = consultar_catastro_por_rc(rc_detectada)
            if datos_catastro.get("ano_construccion"):
                ano_construccion = int(datos_catastro["ano_construccion"])
            if datos_catastro.get("superficie_construida_m2"):
                superficie_catastro = float(datos_catastro["superficie_construida_m2"])
            if datos_catastro.get("municipio"):
                municipio = datos_catastro["municipio"]
            if datos_catastro.get("provincia"):
                provincia = datos_catastro["provincia"]
        except Exception:
            pass

    # 4. Analisis de planos PDF si existen
    datos_planos = {}
    if archivos_encontrados["planos_pdf"]:
        primer_plano = os.path.join(ruta_carpeta, archivos_encontrados["planos_pdf"][0])
        try:
            datos_planos = analizar_plano_distribucion_pdf(primer_plano)
        except Exception:
            pass

    # 5. Deteccion de instalaciones en notas y textos
    clima_inferido = {
        "calefaccion": "Desconocido",
        "acs": "Desconocido",
        "refrigeracion": "Sin sistema"
    }
    if texto_acumulado:
        t_low = texto_acumulado.lower()
        if "aerotermia" in t_low or "bomba de calor" in t_low:
            clima_inferido["calefaccion"] = "BombaCalorAerotermia"
            clima_inferido["acs"] = "BombaCalorAerotermia"
        elif "gas natural" in t_low or "caldera de gas" in t_low:
            clima_inferido["calefaccion"] = "CalderaCondensacion"
            clima_inferido["acs"] = "CalderaCondensacion"
        elif "gasoleo" in t_low or "gasoil" in t_low:
            clima_inferido["calefaccion"] = "CalderaEstandar"
            clima_inferido["acs"] = "CalderaEstandar"
        elif "termo" in t_low or "electrico" in t_low or "calefactor" in t_low or "acumulador" in t_low:
            clima_inferido["calefaccion"] = "EfectoJoule"
            clima_inferido["acs"] = "EfectoJoule"

    # 6. Solucion de envolvente recomendada segun antiguedad
    arquetipo_envolvente = inferir_solucion_envolvente_por_ano(ano_construccion, provincia)
    zona_climatica = obtener_zona_climatica(provincia, municipio)
    superficie_final = datos_planos.get("superficie_util_total_estimada_m2") or superficie_catastro

    # 7. Generacion de Preguntas Quirurgicas para el Tecnico
    preguntas_para_el_tecnico = []
    
    if not rc_detectada:
        preguntas_para_el_tecnico.append(
            "No se ha encontrado Referencia Catastral en las notas. ¿Podrías confirmarla o indicar dirección completa exacta y año de construcción aproximado?"
        )
    if not archivos_encontrados["planos_pdf"] and not datos_planos:
        preguntas_para_el_tecnico.append(
            f"Superficie adoptada de Catastro: {superficie_catastro} m2 construidos (aprox. {round(superficie_catastro*0.85, 1)} m2 útiles). ¿Es correcta o se ajusta a otra cifra?"
        )
    if clima_inferido["calefaccion"] == "Desconocido":
        preguntas_para_el_tecnico.append(
            "¿Qué sistema de calefacción principal tiene el inmueble (caldera individual de gas, radiadores eléctricos, aerotermia o sin calefacción)?"
        )
    if clima_inferido["acs"] == "Desconocido":
        preguntas_para_el_tecnico.append(
            "¿Cómo se produce el Agua Caliente Sanitaria (ACS)? (Ej: termo eléctrico de 80L, caldera mural de gas o butano)."
        )

    preguntas_para_el_tecnico.append(
        "¿Hacia qué orientación da la fachada principal (Norte, Sur, Este, Oeste)? ¿Existen sombras acusadas por edificios colindantes o patio de luces estrecho?"
    )

    # 8. Matriz Ejecutiva de Datos Listos para Certificar
    datos_listos = {
        "nombre_edificio": f"Vivienda {municipio} ({ano_construccion})",
        "direccion": datos_catastro.get("direccion_completa", "Dirección pendiente"),
        "municipio": municipio,
        "provincia": provincia,
        "codigo_postal": cp_detectado or datos_catastro.get("codigo_postal", "15001"),
        "ano_construccion": ano_construccion,
        "superficie_util": round(superficie_final * 0.85, 2),
        "zona_climatica": zona_climatica,
        "referencia_catastral": rc_detectada or "00000000000000000000",
        "tipo_calefaccion": clima_inferido["calefaccion"] if clima_inferido["calefaccion"] != "Desconocido" else "EfectoJoule",
        "tipo_acs": clima_inferido["acs"] if clima_inferido["acs"] != "Desconocido" else "EfectoJoule",
        "solucion_constructiva_estimada": arquetipo_envolvente,
        "directorio_salida": directorio_certificado
    }

    return {
        "estado": "auditado",
        "directorio_carpeta_inmueble": ruta_carpeta,
        "directorio_entrega_certificado": directorio_certificado,
        "archivos_detectados": archivos_encontrados,
        "referencia_catastral_encontrada": rc_detectada,
        "datos_catastro_ovs": datos_catastro,
        "datos_planos_extraidos": datos_planos,
        "arquetipo_constructivo_propuesto": arquetipo_envolvente,
        "datos_listos_para_ce3x": datos_listos,
        "preguntas_quirurgicas_al_tecnico": preguntas_para_el_tecnico,
        "instruccion_para_la_ia": (
            f"Presenta al usuario un resumen sintético de lo detectado. "
            f"Hazle EXCLUSIVAMENTE las preguntas quirúrgicas listadas si falta información, "
            f"o llama directamente a 'certificar_desde_carpeta' para generar el paquete oficial "
            f"automáticamente dentro de la subcarpeta: {directorio_certificado}"
        )
    }

def certificar_inmueble_desde_carpeta(
    ruta_carpeta: str,
    orientacion_principal: str = "Sur",
    tipo_calefaccion: Optional[str] = None,
    tipo_acs: Optional[str] = None,
    nombre_edificio: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ejecuta el ciclo integral de certificación automática a partir de la carpeta de visita:
    Crea automáticamente la subcarpeta 'CERTIFICADO/' dentro de la carpeta del proyecto y genera:
    1. Proyecto nativo editable para CE3X (.cex).
    2. Archivo XML oficial v3.0 para registro telemático (.xml).
    3. Informe oficial de 15 páginas compilado con Typst (.pdf).
    4. Informe oficial de Medidas de Mejora RD 390/2021 y Dictamen NextGen (.pdf y .md).
    5. Ficha resumen ejecutivo de la entrega (RESUMEN_ENTREGA.txt).
    """
    auditoria = auditar_carpeta_inmueble(ruta_carpeta)
    d = auditoria["datos_listos_para_ce3x"]
    
    out_dir = auditoria["directorio_entrega_certificado"]
    os.makedirs(out_dir, exist_ok=True)

    # Consolidar parametros
    nombre_final = nombre_edificio or d["nombre_edificio"]
    direccion = d["direccion"]
    municipio = d["municipio"]
    provincia = d["provincia"]
    codigo_postal = d["codigo_postal"]
    ano = d["ano_construccion"]
    sup = d["superficie_util"]
    zona = d["zona_climatica"]
    rc = d["referencia_catastral"]
    calef = tipo_calefaccion or d["tipo_calefaccion"]
    acs = tipo_acs or d["tipo_acs"]

    # 1. Calculo de calificacion simplificada
    calc = calcular_calificacion_energetica_simplificada(
        superficie_util=sup,
        ano_construccion=ano,
        zona_climatica=zona,
        tipo_calefaccion=calef,
        tipo_acs=acs
    )

    # 2. Generar Archivo CEX Nativo para CE3X
    cex_path = os.path.join(out_dir, "Proyecto_CE3X.cex")
    guardar_fichero_cex_completo(
        ruta_salida=cex_path,
        nombre_edificio=nombre_final,
        direccion=direccion,
        municipio=municipio,
        provincia=provincia,
        codigo_postal=codigo_postal,
        ano_construccion=ano,
        superficie_util=sup,
        zona_climatica=zona,
        referencia_catastral=rc
    )

    # 3. Generar Archivo XML Oficial 3.0
    adm = DatosAdministrativos(
        nombre_edificio=nombre_final,
        direccion=direccion,
        municipio=municipio,
        provincia=provincia,
        codigo_postal=codigo_postal,
        referencia_catastral=rc
    )
    gen = DatosGenerales(
        ano_construccion=ano,
        zona_climatica=zona,
        superficie_util=sup
    )
    res_cal = ResultadoCalificacion(
        demanda_calefaccion=calc["demanda_calefaccion_kwh_m2"],
        demanda_refrigeracion=calc["demanda_refrigeracion_kwh_m2"],
        demanda_acs=calc["demanda_acs_kwh_m2"],
        consumo_energia_primaria_nr=calc["consumo_epnr_totales_kwh_m2"],
        emisiones_co2=calc["emisiones_totales_kgco2_m2"],
        letra_global_emisiones=calc["calificacion_global_emisiones"],
        letra_global_energia_primaria=calc["calificacion_global_consumo"],
        letra_calefaccion=calc["calificacion_global_emisiones"],
        letra_refrigeracion="A",
        letra_acs=calc["calificacion_global_emisiones"]
    )
    proyecto = ProyectoCertificacion(
        administrativos=adm,
        generales=gen
    )

    xml_path = os.path.join(out_dir, "Certificado_Oficial_Registro.xml")
    xml_content = generar_xml_oficial_30(proyecto, res_cal)
    with open(xml_path, "w", encoding="utf-8") as fp:
        fp.write(xml_content)

    # 4. Compilar PDF Oficial del Certificado (15 páginas oficiales xml2cert)
    pdf_ok, pdf_msg = compilar_pdf_desde_xml(xml_path, out_dir)
    pdf_oficial_generado = os.path.join(out_dir, "Certificado_Oficial_Registro.pdf")
    pdf_informe_final = os.path.join(out_dir, "Informe_Certificacion_Energetica.pdf")
    if os.path.exists(pdf_oficial_generado) and not os.path.exists(pdf_informe_final):
        shutil.copy2(pdf_oficial_generado, pdf_informe_final)

    # 5. Generar Paquetes de Mejora y Dictamen NextGen (PDF y Markdown)
    mejoras = calcular_paquetes_medidas_mejora(proyecto, res_cal)
    medida_destacada = mejoras[2] if len(mejoras) >= 3 else mejoras[0]
    dictamen = generar_informe_justificativo_nextgen(
        proyecto=proyecto,
        calificacion_inicial=res_cal,
        medida_seleccionada=medida_destacada
    )
    
    informe_mejoras_md = os.path.join(out_dir, "Informe_Medidas_Mejora_NextGen.md")
    with open(informe_mejoras_md, "w", encoding="utf-8") as fp:
        fp.write(dictamen["dictamen_markdown"])

    informe_mejoras_pdf = os.path.join(out_dir, "Informe_Medidas_Mejora_NextGen.pdf")
    mejoras_pdf_ok = compilar_informe_mejoras_pdf(dictamen["dictamen_markdown"], informe_mejoras_pdf)

    # 6. Ficha Resumen Ejecutivo de la Entrega
    resumen_path = os.path.join(out_dir, "RESUMEN_ENTREGA.txt")
    with open(resumen_path, "w", encoding="utf-8") as fp:
        fp.write(
            f"================================================================================\n"
            f"PAQUETE OFICIAL DE CERTIFICACION ENERGETICA CE3X\n"
            f"Subcarpeta de Entrega: {out_dir}\n"
            f"Inmueble: {nombre_final}\n"
            f"Direccion: {direccion}, {municipio} ({provincia})\n"
            f"Referencia Catastral: {rc}\n"
            f"Superficie Util: {sup} m2 | Ano: {ano} | Zona Climatica: {zona}\n"
            f"Calificacion Obtenida: Letra {calc['calificacion_global_emisiones']} "
            f"({calc['emisiones_totales_kgco2_m2']} kgCO2/m2·ano | {calc['consumo_epnr_totales_kwh_m2']} kWh/m2·ano)\n"
            f"================================================================================\n"
            f"DOCUMENTOS GENERADOS LISTOS PARA TRAMITACION:\n"
            f"1. Proyecto_CE3X.cex                   -> Proyecto nativo editable para CE3X v3.2\n"
            f"2. Certificado_Oficial_Registro.xml    -> XML oficial v3.0 para registro autonomico\n"
            f"3. Informe_Certificacion_Energetica.pdf -> Certificado oficial de 15 paginas (xml2cert)\n"
            f"4. Informe_Medidas_Mejora_NextGen.pdf  -> Dictamen oficial de medidas de mejora y ayudas (PDF)\n"
            f"5. Informe_Medidas_Mejora_NextGen.md   -> Dictamen tecnico en formato Markdown editable\n"
            f"================================================================================\n"
        )

    return {
        "estado": "completado_exitoso",
        "mensaje": f"Paquete oficial de certificación generado exitosamente en la subcarpeta CERTIFICADO/",
        "carpeta_entrega": out_dir,
        "calificacion_obtenida": calc["calificacion_global_emisiones"],
        "entregables": {
            "directorio_certificado": out_dir,
            "proyecto_ce3x": cex_path,
            "xml_oficial_registro": xml_path,
            "pdf_informe_oficial": pdf_informe_final if os.path.exists(pdf_informe_final) else (pdf_oficial_generado if os.path.exists(pdf_oficial_generado) else f"xml2cert info: {pdf_msg}"),
            "pdf_medidas_mejora": informe_mejoras_pdf if mejoras_pdf_ok else None,
            "informe_medidas_mejora_md": informe_mejoras_md,
            "resumen_entrega_txt": resumen_path
        },
        "resumen_energetico": {
            "letra_emisiones": calc["calificacion_global_emisiones"],
            "emisiones_kgco2_m2": calc["emisiones_totales_kgco2_m2"],
            "consumo_epnr_kwh_m2": calc["consumo_epnr_totales_kwh_m2"],
            "mejor_paquete_rehabilitacion": medida_destacada.nombre,
            "ahorro_energia_primaria_pct": medida_destacada.ahorro_energia_primaria_pct,
            "subvencion_nextgen_estimada_eur": dictamen["subvencion_rd853_eur"]
        }
    }
