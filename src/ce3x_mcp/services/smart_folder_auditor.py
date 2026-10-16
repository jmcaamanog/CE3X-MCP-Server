"""
Módulo de Auditoría Inteligente de Carpeta de Visita para CE3X
Analiza de forma autónoma una carpeta de archivos de toma de datos
(croquis, planos PDF, notas de texto, fichas de equipos, modelos BIM)
y genera la matriz de datos técnicos y la entrevista guiada al técnico.
"""

import os
import re
from typing import Dict, Any, List, Optional

from ce3x_mcp.services.catastro import consultar_catastro_por_rc
from ce3x_mcp.services.cte_climate import obtener_zona_climatica, estimar_transmitancias_por_ano
from ce3x_mcp.services.libraries import inferir_solucion_envolvente_por_ano
from ce3x_mcp.services.plan_parser import analizar_plano_distribucion_pdf
from ce3x_mcp.services.equipment_parser import analizar_datos_equipo_climatizacion

REGEX_RC_20 = re.compile(r"\b([0-9]{7}[A-Z]{2}[0-9]{4}[A-Z]{1}[0-9]{4}[A-Z]{2})\b")
REGEX_CP = re.compile(r"\b(0[1-9]|[1-4][0-9]|5[0-2])[0-9]{3}\b")

def auditar_carpeta_inmueble(ruta_carpeta: str) -> Dict[str, Any]:
    """
    Escanea exhaustivamente la carpeta del inmueble, clasifica los archivos disponibles,
    extrae datos catastrales, arquitectonicos e instalaciones, y genera las preguntas
    quirurgicas que la IA debe formular al usuario antes de emitir el certificado.
    """
    if not os.path.exists(ruta_carpeta) or not os.path.isdir(ruta_carpeta):
        raise FileNotFoundError(f"La ruta de carpeta especificada no existe: {ruta_carpeta}")

    # 1. Inventario y clasificacion de archivos
    archivos_encontrados = {
        "textos_y_notas": [],
        "planos_pdf": [],
        "imagenes": [],
        "modelos_bim": []
    }

    for root, _, files in os.walk(ruta_carpeta):
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

    # Si la carpeta misma tiene la RC en el nombre
    if not rc_detectada:
        m_folder = REGEX_RC_20.search(ruta_carpeta)
        if m_folder:
            rc_detectada = m_folder.group(1)

    # 3. Consulta Catastral Automatica
    datos_catastro = {}
    if rc_detectada:
        try:
            datos_catastro = consultar_catastro_por_rc(rc_detectada)
        except Exception as e:
            datos_catastro = {"error": str(e), "referencia": rc_detectada}

    # 4. Analisis de Planos PDF
    datos_planos = []
    superficie_plano = 0.0
    for rel_pdf in archivos_encontrados["planos_pdf"]:
        pdf_full = os.path.join(ruta_carpeta, rel_pdf)
        try:
            res_pdf = analizar_plano_distribucion_pdf(pdf_full)
            if res_pdf.get("superficie_util_total_m2", 0) > 0:
                datos_planos.append(res_pdf)
                superficie_plano = max(superficie_plano, res_pdf["superficie_util_total_m2"])
        except Exception:
            pass

    # 5. Deteccion de Equipos e Instalaciones en texto o PDFs
    clima_inferido = {
        "calefaccion": "Desconocido",
        "acs": "Desconocido",
        "refrigeracion": "No tiene",
        "detalles": []
    }

    t_lower = texto_acumulado.lower()
    if "termo" in t_lower or "eléctrico" in t_lower or "electrico" in t_lower:
        clima_inferido["acs"] = "EfectoJoule"
        clima_inferido["detalles"].append("Termo eléctrico detectado en notas.")
    if "aerotermia" in t_lower or "bomba de calor" in t_lower:
        clima_inferido["calefaccion"] = "BombaDeCalor"
        clima_inferido["acs"] = "BombaDeCalor"
        clima_inferido["detalles"].append("Aerotermia / Bomba de calor mencionada en documentación.")
    elif "gas natural" in t_lower or "caldera mural" in t_lower:
        clima_inferido["calefaccion"] = "CalderaEstandar"
        clima_inferido["acs"] = "CalderaEstandar"
        clima_inferido["detalles"].append("Caldera de gas natural detectada.")

    # 6. Inferencia Bioclimatica y Envolvente Normativa
    provincia = datos_catastro.get("provincia", "A Coruña")
    municipio = datos_catastro.get("municipio", "A Coruña")
    ano_construccion = datos_catastro.get("ano_construccion", 1982)
    superficie_final = superficie_plano if superficie_plano > 0 else datos_catastro.get("superficie_construida_m2", 100.0)

    zona_climatica = obtener_zona_climatica(provincia, municipio)
    arquetipo_envolvente = inferir_solucion_envolvente_por_ano(ano_construccion, provincia)

    # 7. Generacion de Preguntas Quirurgicas (Gap Analysis)
    preguntas_para_el_tecnico = []

    # Pregunta de Carpinteria
    if "rotura" not in t_lower and "rpt" not in t_lower and "pvc" not in t_lower:
        preguntas_para_el_tecnico.append(
            f"En la documentacion se deduce vidrio doble con marco metalico segun el ano ({ano_construccion}). "
            f"¿Las ventanas tienen rotura de puente termico (RPT) o son marco frio? ¿Que color de marco predomina (blanco, gris/oscuro, madera)?"
        )

    # Pregunta de Instalaciones
    if clima_inferido["calefaccion"] == "Desconocido":
        preguntas_para_el_tecnico.append(
            "¿Que sistema de calefaccion principal tiene el inmueble (caldera individual de gas, radiadores electricos, aerotermia o sin calefaccion)?"
        )
    if clima_inferido["acs"] == "Desconocido":
        preguntas_para_el_tecnico.append(
            "¿Como se produce el Agua Caliente Sanitaria (ACS)? (Ej: termo electrico de 80L, caldera mural de gas o butano)."
        )

    # Pregunta de Sombras y Orientacion
    preguntas_para_el_tecnico.append(
        "¿Hacia que orientacion da la fachada principal (Norte, Sur, Este, Oeste)? ¿Existen sombras acusadas por edificios colindantes o patio de luces estrecho?"
    )

    # 8. Matriz Ejecutiva de Datos Listos para Certificar
    datos_listos = {
        "nombre_edificio": f"Vivienda {municipio} ({ano_construccion})",
        "direccion": datos_catastro.get("direccion_completa", "Direccion pendiente"),
        "municipio": municipio,
        "provincia": provincia,
        "codigo_postal": cp_detectado or datos_catastro.get("codigo_postal", "15001"),
        "ano_construccion": ano_construccion,
        "superficie_util": round(superficie_final * 0.85, 2),  # Estimacion util a partir de construida si aplica
        "zona_climatica": zona_climatica,
        "referencia_catastral": rc_detectada or "00000000000000000000",
        "tipo_calefaccion": clima_inferido["calefaccion"] if clima_inferido["calefaccion"] != "Desconocido" else "EfectoJoule",
        "tipo_acs": clima_inferido["acs"] if clima_inferido["acs"] != "Desconocido" else "EfectoJoule",
        "solucion_constructiva_estimada": arquetipo_envolvente
    }

    return {
        "estado": "auditado",
        "archivos_detectados": archivos_encontrados,
        "referencia_catastral_encontrada": rc_detectada,
        "datos_catastro_ovs": datos_catastro,
        "datos_planos_extraidos": datos_planos,
        "arquetipo_constructivo_propuesto": arquetipo_envolvente,
        "datos_listos_para_ce3x": datos_listos,
        "preguntas_quirurgicas_al_tecnico": preguntas_para_el_tecnico,
        "instruccion_para_la_ia": (
            "Presenta al usuario un resumen sintetico de lo detectado en la carpeta y hazle "
            "EXCLUSIVAMENTE las preguntas quirurgicas listadas. En cuanto el usuario responda, "
            "llama directamente a 'generar_certificado_completo' con los parametros consolidados."
        )
    }
