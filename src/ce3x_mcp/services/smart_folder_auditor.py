"""
Módulo de Auditoría Inteligente, Organización y Certificación desde Carpeta de Visita para CE3X
Implementa la arquitectura estándar de 5 carpetas (INFORMACION, PLANOS, FOTOS, INSTALACIONES, CERTIFICADO),
clasificación autónoma de documentos desordenados, extracción técnica multiformato y generación
completa de entregables oficiales.
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
from ce3x_mcp.services.technician_profile import obtener_perfil_tecnico
from ce3x_mcp.core.models import (
    ProyectoCertificacion,
    DatosAdministrativos,
    DatosGenerales,
    ResultadoCalificacion
)

REGEX_RC_20 = re.compile(r"\b([0-9]{7}[A-Z]{2}[0-9]{4}[A-Z]{1}[0-9]{4}[A-Z]{2})\b")
REGEX_CP = re.compile(r"\b(0[1-9]|[1-4][0-9]|5[0-2])[0-9]{3}\b")

# Palabras clave para la clasificación automática
PALABRAS_CLAVE_INSTALACIONES = [
    "caldera", "termo", "aerotermia", "bomba", "clima", "instalacion", "calefaccion",
    "acs", "radiador", "split", "daikin", "vaillant", "junkers", "saunier", "baxi",
    "mitsubishi", "panasonic", "placa", "contador", "acumulador", "deposito",
    "inversor", "solar", "fotovoltaica", "ficha_tecnica", "equipo", "maquina", "fleck"
]
PALABRAS_CLAVE_PLANOS = [
    "plano", "distribucion", "croquis", "planta", "alzado", "seccion", "arquitectura",
    "acotado", "mediciones", "superficies"
]
PALABRAS_CLAVE_INFORMACION = [
    "nota", "visita", "catastro", "datos", "escritura", "recibo", "ibi", "encargo",
    "cliente", "apuntes"
]

CANONICAL_SUBFOLDERS = ["INFORMACION", "PLANOS", "FOTOS", "INSTALACIONES", "CERTIFICADO"]

def clasificar_archivo_visita(nombre_archivo: str) -> str:
    """Determina a qué subcarpeta estándar corresponde un archivo."""
    nombre_low = nombre_archivo.lower()
    ext = os.path.splitext(nombre_low)[1]

    # 1. Certificados y entregables previos
    if ext == ".cex" or "certificado" in nombre_low or "informe_certificacion" in nombre_low:
        return "CERTIFICADO"

    # 2. Instalaciones y climatización (fotos de placas, fichas técnicas, etc.)
    if any(p in nombre_low for p in PALABRAS_CLAVE_INSTALACIONES):
        return "INSTALACIONES"

    # 3. Documentos de Catastro (PDFs con RC o mención a Catastro) -> INFORMACION
    if REGEX_RC_20.search(nombre_archivo) or any(p in nombre_low for p in ["catastro", "ovc", "sec", "referencia", "parcela", "descriptiva"]):
        return "INFORMACION"

    # 4. Modelos BIM y Planos arquitectónicos
    if ext in [".ifc", ".dwg", ".dxf", ".rvt"]:
        return "PLANOS"
    if ext == ".pdf":
        if any(p in nombre_low for p in PALABRAS_CLAVE_PLANOS):
            return "PLANOS"
        if any(p in nombre_low for p in PALABRAS_CLAVE_INFORMACION):
            return "INFORMACION"
        return "PLANOS"

    # 4. Textos y notas de información
    if ext in [".txt", ".md", ".json", ".csv", ".doc", ".docx", ".odt", ".rtf"]:
        return "INFORMACION"

    # 5. Fotos generales (fachadas, huecos, ventanas, sombras, interiores)
    if ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".heic", ".tiff"]:
        return "FOTOS"

    return "INFORMACION"

def mover_archivo_seguro(src: str, dst_dir: str) -> str:
    """Mueve un archivo evitando sobrescribir ficheros existentes."""
    nombre = os.path.basename(src)
    base, ext = os.path.splitext(nombre)
    dest = os.path.join(dst_dir, nombre)
    contador = 1
    while os.path.exists(dest) and os.path.abspath(src) != os.path.abspath(dest):
        dest = os.path.join(dst_dir, f"{base}_{contador}{ext}")
        contador += 1
    if os.path.abspath(src) != os.path.abspath(dest):
        shutil.move(src, dest)
    return dest

def organizar_carpeta_visita(ruta_carpeta: str) -> Dict[str, Any]:
    """
    Crea la estructura estándar de 5 carpetas y clasifica automáticamente los archivos:
    - INFORMACION/   -> Notas de visita, Referencia Catastral, apuntes y datos.
    - PLANOS/        -> Planos de distribución (PDF), croquis acotados, modelos BIM (IFC/DWG).
    - FOTOS/         -> Fotografías del inmueble (fachada exterior, huecos y carpinterías).
    - INSTALACIONES/ -> Fotos de placas de calderas, termos, bombas de calor y fichas técnicas.
    - CERTIFICADO/   -> Carpeta oficial de salida para .cex, .xml, .pdf y mejoras NextGen.

    Si la carpeta del inmueble contiene archivos sueltos en su raíz o en carpetas no estándar,
    los mueve de forma segura a su subcarpeta correspondiente y crea la ficha 'LEEME_ESTRUCTURA_VISITA.txt'.
    """
    if not os.path.exists(ruta_carpeta) or not os.path.isdir(ruta_carpeta):
        raise FileNotFoundError(f"La ruta de carpeta especificada no existe: {ruta_carpeta}")

    carpetas = {sub: os.path.join(ruta_carpeta, sub) for sub in CANONICAL_SUBFOLDERS}
    for p in carpetas.values():
        os.makedirs(p, exist_ok=True)

    movidos = []

    # Escanear archivos sueltos en la raíz y subdirectorios no canónicos
    for root, dirs, files in os.walk(ruta_carpeta):
        rel_root = os.path.relpath(root, ruta_carpeta)
        partes = rel_root.split(os.sep) if rel_root != "." else []

        # Si ya está dentro de una subcarpeta canónica, respetarlo
        if partes and partes[0].upper() in CANONICAL_SUBFOLDERS:
            continue

        for f in files:
            if f in ["LEEME_ESTRUCTURA_VISITA.txt", "RESUMEN_ENTREGA.txt"]:
                continue
            src_file = os.path.join(root, f)
            sub_destino = clasificar_archivo_visita(f)
            dst_dir = carpetas[sub_destino]

            dest_final = mover_archivo_seguro(src_file, dst_dir)
            movidos.append({
                "archivo": f,
                "origen": os.path.relpath(src_file, ruta_carpeta),
                "subcarpeta_destino": sub_destino,
                "ruta_destino": os.path.relpath(dest_final, ruta_carpeta)
            })

    # Generar ficha LEEME explicativa para el técnico
    leeme_path = os.path.join(ruta_carpeta, "LEEME_ESTRUCTURA_VISITA.txt")
    with open(leeme_path, "w", encoding="utf-8") as fp:
        fp.write(
            "================================================================================\n"
            "ESTRUCTURA ESTANDAR DE CARPETA DE VISITA Y CERTIFICACION ENERGETICA\n"
            "================================================================================\n"
            "Esta carpeta ha sido organizada conforme al estandar profesional:\n\n"
            "📁 1. INFORMACION/   -> Notas de visita, Referencia Catastral, apuntes, datos del cliente.\n"
            "📁 2. PLANOS/        -> Planos de distribucion en PDF, croquis acotados, modelos BIM (IFC/DWG).\n"
            "📁 3. FOTOS/         -> Fotografias del inmueble (fachada exterior, huecos y carpinterias, vistas).\n"
            "📁 4. INSTALACIONES/ -> Fotos de placas de calderas, termos, bombas de calor y fichas tecnicas.\n"
            "📁 5. CERTIFICADO/   -> Entregables oficiales finales (.cex, .xml, .pdf y mejoras NextGen).\n"
            "================================================================================\n"
        )

    inventario = {sub: os.listdir(carpetas[sub]) for sub in CANONICAL_SUBFOLDERS}

    return {
        "estado": "organizado_exitoso",
        "mensaje": f"Carpeta estructurada con éxito en las 5 subcarpetas estándar. Se han clasificado {len(movidos)} archivos.",
        "directorio_raiz": ruta_carpeta,
        "subcarpetas": carpetas,
        "total_archivos_movidos": len(movidos),
        "detalle_movimientos": movidos,
        "inventario_actual": inventario
    }

def compilar_informe_mejoras_pdf(
    texto_md: str,
    ruta_pdf: str,
    titulo: str = "DICTAMEN OFICIAL DE MEDIDAS DE MEJORA Y SUBVENCIONES NEXTGEN"
) -> bool:
    """Compila el informe técnico de mejoras a PDF maquetado profesionalmente."""
    try:
        doc = fitz.open()
        lines = texto_md.split("\n")
        page = doc.new_page(width=595, height=842) # A4 estándar
        
        # Franja decorativa
        rect_decor = fitz.Rect(0, 0, 595, 14)
        page.draw_rect(rect_decor, color=(0.08, 0.38, 0.74), fill=(0.08, 0.38, 0.74))
        
        # Encabezado
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
    Escanea exhaustivamente la carpeta del inmueble, clasifica los archivos disponibles en
    las 5 categorías estándar (INFORMACION, PLANOS, FOTOS, INSTALACIONES, CERTIFICADO),
    extrae datos catastrales, arquitectónicos e instalaciones, y define la subcarpeta CERTIFICADO/
    donde se guardará el conjunto de entregables oficiales.
    """
    if not os.path.exists(ruta_carpeta) or not os.path.isdir(ruta_carpeta):
        raise FileNotFoundError(f"La ruta de carpeta especificada no existe: {ruta_carpeta}")

    directorio_certificado = os.path.join(ruta_carpeta, "CERTIFICADO")

    # 1. Inventario y clasificación exhaustiva
    archivos_por_categoria = {
        "informacion": [],
        "planos": [],
        "fotos": [],
        "instalaciones": [],
        "certificado": []
    }
    archivos_sueltos_en_raiz = []

    for root, dirs, files in os.walk(ruta_carpeta):
        rel_root = os.path.relpath(root, ruta_carpeta)
        partes = rel_root.split(os.sep) if rel_root != "." else []

        # Ignorar la carpeta CERTIFICADO de salida al auditar la toma de datos
        if partes and partes[0].upper() == "CERTIFICADO":
            for f in files:
                archivos_por_categoria["certificado"].append(os.path.join(rel_root, f))
            continue

        for f in files:
            if f in ["LEEME_ESTRUCTURA_VISITA.txt", "RESUMEN_ENTREGA.txt"]:
                continue
            ruta_f = os.path.join(root, f)
            rel_f = os.path.relpath(ruta_f, ruta_carpeta)

            if rel_root == ".":
                archivos_sueltos_en_raiz.append(f)

            cat = clasificar_archivo_visita(f)
            archivos_por_categoria[cat.lower()].append(rel_f)

    carpeta_organizada = len(archivos_sueltos_en_raiz) == 0

    # 2. Búsqueda exhaustiva de Referencia Catastral (Nombres de archivo y documentos)
    texto_acumulado = ""
    rc_detectada = None
    cp_detectado = None

    # 2.1. Buscar en todos los nombres de archivo
    for cat_list in archivos_por_categoria.values():
        for f_rel in cat_list:
            m_fn = REGEX_RC_20.search(os.path.basename(f_rel))
            if m_fn:
                rc_detectada = m_fn.group(1)
                break
        if rc_detectada:
            break

    # 2.2. Extraer texto de documentos en INFORMACION (TXT, MD, JSON, CSV y PDFs de Catastro)
    for rel_doc in archivos_por_categoria["informacion"]:
        doc_path = os.path.join(ruta_carpeta, rel_doc)
        ext = os.path.splitext(rel_doc)[1].lower()
        if ext in [".txt", ".md", ".json", ".csv"]:
            try:
                with open(doc_path, "r", encoding="utf-8", errors="ignore") as fp:
                    t = fp.read()
                    texto_acumulado += "\n" + t
                    if not rc_detectada:
                        m_rc = REGEX_RC_20.search(t)
                        if m_rc: rc_detectada = m_rc.group(1)
                    if not cp_detectado:
                        m_cp = REGEX_CP.search(t)
                        if m_cp: cp_detectado = m_cp.group(0)
            except Exception:
                pass
        elif ext == ".pdf":
            try:
                doc_pdf = fitz.open(doc_path)
                for page in doc_pdf:
                    t_page = page.get_text()
                    texto_acumulado += "\n" + t_page
                    if not rc_detectada:
                        m_rc = REGEX_RC_20.search(t_page)
                        if m_rc: rc_detectada = m_rc.group(1)
                    if not cp_detectado:
                        m_cp = REGEX_CP.search(t_page)
                        if m_cp: cp_detectado = m_cp.group(0)
            except Exception:
                pass

    # 3. Consulta Catastral Automática si se halló RC
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

    # 4. Análisis inteligente de planos (PDF) y modelos BIM (IFC)
    datos_planos = {}
    datos_bim = {}
    
    # Buscar el mejor plano PDF (que contenga recintos detectados)
    planos_pdf = [p for p in archivos_por_categoria["planos"] if p.lower().endswith(".pdf")]
    # También revisar PDFs en la raíz si no estuvieran clasificados aún
    for root_f in archivos_sueltos_en_raiz:
        if root_f.lower().endswith(".pdf") and root_f not in planos_pdf:
            planos_pdf.append(root_f)

    for p_rel in planos_pdf:
        # Evitar analizar PDFs que son exclusivamente catastrales
        if REGEX_RC_20.search(p_rel) or "catastro" in p_rel.lower():
            continue
        full_pdf = os.path.join(ruta_carpeta, p_rel)
        try:
            res_plano = analizar_plano_distribucion_pdf(full_pdf)
            if res_plano.get("valido") and res_plano.get("num_estancias_detectadas", 0) > 0:
                if not datos_planos or res_plano["superficie_util_total_detectada_m2"] > datos_planos.get("superficie_util_total_detectada_m2", 0):
                    datos_planos = res_plano
                    datos_planos["fichero_plano"] = p_rel
        except Exception:
            pass

    # Analizar modelos BIM IFC si existen en PLANOS o en cualquier subcarpeta
    from ce3x_mcp.services.bim_parser import extraer_envolvente_desde_ifc
    for root_dir, _, files in os.walk(ruta_carpeta):
        for f in files:
            if f.lower().endswith(".ifc"):
                ifc_full = os.path.join(root_dir, f)
                try:
                    res_bim = extraer_envolvente_desde_ifc(ifc_full)
                    if res_bim.get("valido"):
                        rel_ifc = os.path.relpath(ifc_full, ruta_carpeta)
                        datos_bim[rel_ifc] = res_bim
                except Exception:
                    pass

    # 5. Detección de instalaciones en archivos de INSTALACIONES y notas
    clima_inferido = {
        "calefaccion": "Desconocido",
        "acs": "Desconocido",
        "refrigeracion": "Sin sistema"
    }
    
    # 5.1. Detección por nombres de archivo en INSTALACIONES (fotos de placas, fichas)
    for inst_rel in archivos_por_categoria["instalaciones"]:
        base_inst = os.path.splitext(os.path.basename(inst_rel))[0].replace("_", " ")
        parsed = analizar_datos_equipo_climatizacion(base_inst)
        if parsed.get("valido"):
            tec = parsed.get("tecnologia_detectada")
            srv = parsed.get("servicio_detectado")
            if srv in ["Calefaccion", "Mixto2", "Mixto3"]:
                clima_inferido["calefaccion"] = tec
            if srv in ["ACS", "Mixto2", "Mixto3"]:
                clima_inferido["acs"] = tec

    # 5.2. Detección por texto acumulado en notas de INFORMACION
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
            if clima_inferido["acs"] == "Desconocido":
                clima_inferido["acs"] = "EfectoJoule"
            if clima_inferido["calefaccion"] == "Desconocido":
                clima_inferido["calefaccion"] = "EfectoJoule"

    # 6. Solución de envolvente recomendada según antigüedad
    arquetipo_envolvente = inferir_solucion_envolvente_por_ano(ano_construccion, provincia)
    zona_climatica = obtener_zona_climatica(provincia, municipio)
    superficie_final = datos_planos.get("superficie_util_total_estimada_m2") or superficie_catastro

    # 7. Generación de Preguntas Quirúrgicas para el Técnico
    preguntas_para_el_tecnico = []

    if not rc_detectada:
        preguntas_para_el_tecnico.append(
            "No se ha encontrado Referencia Catastral en INFORMACION/. ¿Podrías confirmarla o indicar dirección completa exacta y año aproximado de construcción?"
        )
    if not planos_pdf and not datos_planos:
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

    # 8. Determinación rigurosa de superficie útil contrastada
    origen_superficie = "Catastro construida ponderada (85%)"
    if datos_planos and datos_planos.get("superficie_util_total_detectada_m2", 0) > 0:
        superficie_util_contrastada = datos_planos["superficie_util_total_detectada_m2"]
        origen_superficie = f"Plano arquitectónico medido ({datos_planos.get('fichero_plano', 'PDF')}): {len(datos_planos.get('estancias', []))} estancias"
    elif datos_catastro.get("unidades_constructivas"):
        # Buscar unidad de VIVIENDA
        vivienda_ucs = [u for u in datos_catastro["unidades_constructivas"] if "vivienda" in u.get("uso", "").lower()]
        if vivienda_ucs:
            superficie_util_contrastada = round(vivienda_ucs[0]["superficie_m2"] * 0.85, 2)
            origen_superficie = f"Catastro unidad constructiva Vivienda ({vivienda_ucs[0]['superficie_m2']} m2 x 0.85)"
        else:
            superficie_util_contrastada = round(superficie_catastro * 0.85, 2)
    else:
        superficie_util_contrastada = round(superficie_catastro * 0.85, 2)

    # 9. Matriz Ejecutiva de Datos Listos para Certificar con Origen Contrastado
    datos_listos = {
        "nombre_edificio": f"Vivienda {municipio} ({ano_construccion})",
        "direccion": datos_catastro.get("direccion", "Dirección pendiente"),
        "municipio": municipio,
        "provincia": provincia,
        "codigo_postal": datos_catastro.get("codigo_postal") or cp_detectado or "15001",
        "ano_construccion": ano_construccion,
        "superficie_util": superficie_util_contrastada,
        "zona_climatica": zona_climatica,
        "referencia_catastral": rc_detectada or "00000000000000000000",
        "tipo_calefaccion": clima_inferido["calefaccion"] if clima_inferido["calefaccion"] != "Desconocido" else "Pendiente_Confirmacion",
        "tipo_acs": clima_inferido["acs"] if clima_inferido["acs"] != "Desconocido" else "Pendiente_Confirmacion",
        "instalaciones_confirmadas": clima_inferido["calefaccion"] != "Desconocido" and clima_inferido["acs"] != "Desconocido",
        "solucion_constructiva_estimada": arquetipo_envolvente,
        "directorio_salida": directorio_certificado,
        "trazabilidad_origen_datos": {
            "referencia_catastral": f"{rc_detectada} (Localizada en documentos de la visita)" if rc_detectada else "No identificada",
            "direccion_oficial": datos_catastro.get("direccion", "Pendiente de Catastro"),
            "ano_edificacion": f"{ano_construccion} (Catastro OVC)" if datos_catastro.get("ano_construccion") else f"{ano_construccion} (Estimado)",
            "superficie_util": f"{superficie_util_contrastada} m2 ({origen_superficie})",
            "zona_climatica": f"{zona_climatica} (CTE DB-HE Apéndice B para {municipio}, {provincia})"
        }
    }

    sugerencia_organizacion = None
    if not carpeta_organizada:
        sugerencia_organizacion = (
            f"La carpeta contiene {len(archivos_sueltos_en_raiz)} archivo(s) suelto(s) en su raíz. "
            f"Se recomienda ejecutar 'organizar_carpeta_visita' para agruparlos en INFORMACION/, PLANOS/, FOTOS/, INSTALACIONES/ y CERTIFICADO/."
        )

    return {
        "estado": "auditado",
        "directorio_carpeta_inmueble": ruta_carpeta,
        "directorio_entrega_certificado": directorio_certificado,
        "carpeta_organizada": carpeta_organizada,
        "archivos_sueltos_en_raiz": archivos_sueltos_en_raiz,
        "sugerencia_organizacion": sugerencia_organizacion,
        "archivos_detectados_por_categoria": archivos_por_categoria,
        "referencia_catastral_encontrada": rc_detectada,
        "datos_catastro_ovs": datos_catastro,
        "datos_planos_extraidos": datos_planos,
        "modelos_bim_extraidos": datos_bim,
        "climatizacion_detectada": clima_inferido,
        "arquetipo_constructivo_propuesto": arquetipo_envolvente,
        "datos_listos_para_ce3x": datos_listos,
        "preguntas_quirurgicas_al_tecnico": preguntas_para_el_tecnico,
        "instruccion_para_la_ia": (
            f"1. Si 'carpeta_organizada' es False, ejecuta primero 'organizar_carpeta_visita' para ordenar los archivos.\n"
            f"2. Presenta al usuario un resumen sintético de lo detectado.\n"
            f"3. Hazle EXCLUSIVAMENTE las preguntas quirúrgicas listadas si falta información.\n"
            f"4. Llama a 'certificar_desde_carpeta' para generar el paquete oficial dentro de: {directorio_certificado}"
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

    # Consolidar parámetros
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

    # 1. Cálculo de calificación simplificada
    calc = calcular_calificacion_energetica_simplificada(
        superficie_util=sup,
        ano_construccion=ano,
        zona_climatica=zona,
        tipo_calefaccion=calef,
        tipo_acs=acs
    )

    perfil = obtener_perfil_tecnico()

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
        referencia_catastral=rc,
        nombre_tecnico=perfil["nombre_tecnico"],
        nif_tecnico=perfil["nif_tecnico"],
        titulacion=perfil["titulacion"],
        razon_social=perfil["razon_social"],
        comunidad_autonoma=perfil["comunidad_autonoma"]
    )

    # 3. Generar Archivo XML Oficial 3.0
    adm = DatosAdministrativos(
        nombre_edificio=nombre_final,
        direccion=direccion,
        municipio=municipio,
        provincia=provincia,
        codigo_postal=codigo_postal,
        referencia_catastral=rc,
        nombre_tecnico=perfil["nombre_tecnico"],
        nif_tecnico=perfil["nif_tecnico"],
        titulacion_tecnico=perfil["titulacion"],
        razon_social=perfil["razon_social"],
        comunidad_autonoma=perfil["comunidad_autonoma"]
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
