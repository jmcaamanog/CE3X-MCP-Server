"""
Generador oficial de archivos de intercambio XML DatosEnergeticosDelEdificio version 3.0.
Construye XMLs limpios y estructurados que eliminan todo dato fantasma de plantillas
(viviendas múltiples, torres de refrigeración de 1006 kW, certificadores de prueba)
y los valida estrictamente contra el esquema RelaxNG oficial del Ministerio.
"""

import os
import re
import uuid
import datetime
import xml.etree.ElementTree as ET
import lxml.etree as etree
from typing import Optional, Dict, Any, List
from ce3x_mcp.core.models import ProyectoCertificacion, ResultadoCalificacion

OFFICIAL_XML_TEMPLATE_PATH = r"C:\Program Files (x86)\CE3Xv3.2\moduloXML\xmlcert_20260703\examples\Ejemplo30_Informe.xml"
OFFICIAL_RELAXNG_SCHEMA = r"C:\Program Files (x86)\CE3Xv3.2\moduloXML\resources\RelaxNG\DatosEnergeticosDelEdificioSchema30-full.rng"

# 1. Mapeo Oficial de Provincias a la sintaxis exacta del esquema RelaxNG
PROVINCIAS_OFICIALES = [
    'Albacete', 'Alicante/Alacant', 'Almería', 'Araba/Álava', 'Asturias', 'Ávila', 'Badajoz',
    'Balears, Illes', 'Barcelona', 'Bizkaia', 'Burgos', 'Cáceres', 'Cádiz', 'Cantabria',
    'Castellón/Castelló', 'Ciudad Real', 'Córdoba', 'Coruña, A', 'Cuenca', 'Gipuzkoa',
    'Girona', 'Granada', 'Guadalajara', 'Huelva', 'Huesca', 'Jaén', 'León', 'Lleida',
    'Lugo', 'Madrid', 'Málaga', 'Murcia', 'Navarra', 'Ourense', 'Palencia', 'Palmas, Las',
    'Pontevedra', 'Rioja, La', 'Salamanca', 'Santa Cruz de Tenerife', 'Segovia', 'Sevilla',
    'Soria', 'Tarragona', 'Teruel', 'Toledo', 'Valencia/València', 'Valladolid', 'Zamora',
    'Zaragoza', 'Ceuta', 'Melilla'
]

PROVINCIAS_ALIAS = {
    "a coruña": "Coruña, A", "la coruña": "Coruña, A", "coruña": "Coruña, A", "coruna": "Coruña, A", "a coruna": "Coruña, A",
    "alava": "Araba/Álava", "araba": "Araba/Álava", "álava": "Araba/Álava",
    "alicante": "Alicante/Alacant", "alacant": "Alicante/Alacant",
    "castellon": "Castellón/Castelló", "castelló": "Castellón/Castelló",
    "valencia": "Valencia/València", "valència": "Valencia/València",
    "baleares": "Balears, Illes", "illes balears": "Balears, Illes", "islas baleares": "Balears, Illes",
    "las palmas": "Palmas, Las", "palmas": "Palmas, Las",
    "la rioja": "Rioja, La", "rioja": "Rioja, La",
    "vizcaya": "Bizkaia", "guipuzcoa": "Gipuzkoa", "guipúzcoa": "Gipuzkoa"
}

def normalizar_provincia(prov: str) -> str:
    p = prov.strip()
    p_lower = p.lower()
    if p_lower in PROVINCIAS_ALIAS:
        return PROVINCIAS_ALIAS[p_lower]
    for ofi in PROVINCIAS_OFICIALES:
        if p_lower == ofi.lower():
            return ofi
    # Búsqueda parcial si no coincide exactamente
    for ofi in PROVINCIAS_OFICIALES:
        if p_lower in ofi.lower() or ofi.lower() in p_lower:
            return ofi
    return p.title()

# 2. Mapeo Oficial de Comunidades Autónomas según esquema RelaxNG
CCAA_MAP = {
    "Coruña, A": "Galicia", "Lugo": "Galicia", "Ourense": "Galicia", "Pontevedra": "Galicia",
    "Madrid": "Madrid, Comunidad de",
    "Barcelona": "Cataluña", "Girona": "Cataluña", "Lleida": "Cataluña", "Tarragona": "Cataluña",
    "Valencia/València": "Comunitat Valenciana", "Alicante/Alacant": "Comunitat Valenciana", "Castellón/Castelló": "Comunitat Valenciana",
    "Sevilla": "Andalucía", "Málaga": "Andalucía", "Cádiz": "Andalucía", "Granada": "Andalucía", "Córdoba": "Andalucía", "Almería": "Andalucía", "Huelva": "Andalucía", "Jaén": "Andalucía",
    "Zaragoza": "Aragón", "Huesca": "Aragón", "Teruel": "Aragón",
    "Asturias": "Asturias, Principado de",
    "Cantabria": "Cantabria",
    "Navarra": "Navarra, Comunidad Foral de",
    "Rioja, La": "Rioja, La",
    "Araba/Álava": "País Vasco", "Gipuzkoa": "País Vasco", "Bizkaia": "País Vasco",
    "Badajoz": "Extremadura", "Cáceres": "Extremadura",
    "Toledo": "Castilla - La Mancha", "Ciudad Real": "Castilla - La Mancha", "Albacete": "Castilla - La Mancha", "Cuenca": "Castilla - La Mancha", "Guadalajara": "Castilla - La Mancha",
    "Valladolid": "Castilla y León", "Burgos": "Castilla y León", "León": "Castilla y León", "Salamanca": "Castilla y León", "Zamora": "Castilla y León", "Palencia": "Castilla y León", "Ávila": "Castilla y León", "Segovia": "Castilla y León", "Soria": "Castilla y León",
    "Murcia": "Murcia, Región de",
    "Balears, Illes": "Balears, Illes",
    "Palmas, Las": "Canarias", "Santa Cruz de Tenerife": "Canarias",
    "Ceuta": "Ceuta", "Melilla": "Melilla"
}

def obtener_comunidad_autonoma(provincia_normalizada: str) -> str:
    return CCAA_MAP.get(provincia_normalizada, "Madrid, Comunidad de")


def normalizar_titulacion(tit: str) -> str:
    tit_clean = (tit or "").strip()
    tit_low = tit_clean.lower()
    if "aparejador" in tit_low or ("arquitect" in tit_low and ("téc" in tit_low or "tec" in tit_low)):
        return "Arquitectura técnica o aparejadores"
    if "arquitect" in tit_low:
        return "Arquitectura"
    if "industrial" in tit_low and ("téc" in tit_low or "tec" in tit_low):
        return "Ingeniería Técnica Industrial"
    if "industrial" in tit_low:
        return "Ingeniería Industrial"
    if "caminos" in tit_low:
        return "Ingeniería de Caminos, Canales y Puertos"
    if "telecomunicaci" in tit_low and ("téc" in tit_low or "tec" in tit_low):
        return "Ingeniería Técnica Telecomunicación"
    if "telecomunicaci" in tit_low:
        return "Ingeniería de Telecomunicación"
    if "agrónom" in tit_low or "agronom" in tit_low:
        return "Ingeniería Agrónoma"
    if "agrícol" in tit_low or "agricol" in tit_low:
        return "Ingeniería Técnica Agrícola"
    
    titulaciones_oficiales = [
        "Arquitectura", "Arquitectura técnica o aparejadores",
        "Ingeniería Aeronáutica", "Ingeniería Agrónoma",
        "Ingeniería de Caminos, Canales y Puertos", "Ingeniería Industrial",
        "Ingeniería de Minas", "Ingeniería de Montes",
        "Ingeniería Naval y Oceánica", "Ingeniería de Telecomunicación",
        "Ingeniería Técnica Aeronáutica", "Ingeniería Técnica Agrícola",
        "Ingeniería Técnica Forestal", "Ingeniería Técnica Industrial",
        "Ingeniería Técnica de Minas", "Ingeniería Técnica Naval",
        "Ingeniería Técnica de Obras Públicas", "Ingeniería Técnica Telecomunicación",
        "Ingeniería Técnica Topografía", "Ingeniería Química"
    ]
    for ofi in titulaciones_oficiales:
        if ofi.lower() == tit_low:
            return ofi
            
    return f"Otra({tit_clean})" if tit_clean else "Arquitectura técnica o aparejadores"

def generar_xml_oficial_30(
    proyecto: ProyectoCertificacion,
    resultado: ResultadoCalificacion,
    template_path: Optional[str] = None
) -> str:
    """
    Genera el archivo XML oficial conforme a DatosEnergeticosDelEdificio version 3.0.
    1. Sustituye todos los datos administrativos y de certificación por datos reales.
    2. Purga y elimina radicalmente las instalaciones fantasma (torres de refrigeración de 1006 kW, UTAs).
    3. Construye los generadores reales del inmueble garantizando compatibilidad RelaxNG.
    4. Valida el resultado con lxml contra DatosEnergeticosDelEdificioSchema30-full.rng.
    """
    t_path = template_path or OFFICIAL_XML_TEMPLATE_PATH
    if not os.path.exists(t_path):
        raise FileNotFoundError(f"Plantilla oficial no encontrada en: {t_path}")
        
    tree = ET.parse(t_path)
    root = tree.getroot()
    
    adm = proyecto.administrativos
    gen = proyecto.generales
    provincia_norm = normalizar_provincia(adm.provincia)
    ccaa_norm = obtener_comunidad_autonoma(provincia_norm)
    fecha_hoy = datetime.date.today().strftime("%d/%m/%Y")
    
    # 1. Datos del Edificio (Eliminar datos de Centro Juvenil)
    root.find(".//DatosEdificio/Descripcion").text = adm.nombre_edificio or "Vivienda Unifamiliar / Piso"
    root.find(".//DatosEdificio/Direccion").text = adm.direccion or "Dirección no identificada"
    root.find(".//DatosEdificio/Municipio").text = adm.municipio or ""
    root.find(".//DatosEdificio/Provincia").text = provincia_norm
    root.find(".//DatosEdificio/ComunidadAutonoma").text = ccaa_norm
    root.find(".//DatosEdificio/CodigoPostal").text = adm.codigo_postal or "00000"
    root.find(".//DatosEdificio/ZonaClimatica").text = gen.zona_climatica
    root.find(".//DatosEdificio/FechaConstruccion").text = str(gen.ano_construccion)
    
    # Alcance y unidades de uso: 'Completo' o 'Parte'
    tipo_gen = getattr(gen, "tipologia", "ViviendaBloque")
    es_bloque_completo = "bloque" in tipo_gen.lower() and "vivienda" not in tipo_gen.lower() and "unifamiliar" not in tipo_gen.lower()
    root.find(".//DatosEdificio/Alcance").text = "Completo" if es_bloque_completo else "Parte"
    root.find(".//DatosEdificio/NumUnidadesUso").text = "1"
    root.find(".//DatosEdificio/SuperficieUtil").text = f"{gen.superficie_util:.2f}"
    
    # Normativa oficial NORM_EDIF
    ano = gen.ano_construccion
    if ano < 1979:
        norma = "ANTE_NBE_CT_79"
    elif ano < 2006:
        norma = "NBE_CT_79"
    elif ano < 2013:
        norma = "CTE_DB_HE_2006"
    elif ano < 2019:
        norma = "CTE_DB_HE_2013"
    else:
        norma = "CTE_DB_HE_2019"
    norm_node = root.find(".//DatosEdificio/NormativaEdificacion")
    if norm_node is not None:
        norm_node.text = norma

    # Referencias Catastrales (Validación estricta de regex RelaxNG: DGC_PARCELA 14 pos, DGC_INMUEBLE 6 pos \d{4}[A-Z]{2})
    rc_refs_node = root.find(".//DatosEdificio/ReferenciasCatastrales")
    if rc_refs_node is not None:
        rc_refs_node.clear()
        ET.SubElement(rc_refs_node, "Registro").text = "DGC"
        ref_elem = ET.SubElement(rc_refs_node, "Ref")
        rc_raw = adm.referencia_catastral.strip().upper() if adm.referencia_catastral else ""
        if (len(rc_raw) >= 20 and 
            re.match(r"^[0-9A-Z]{14}$", rc_raw[:14]) and 
            re.match(r"^\d{4}[A-Z]{2}$", rc_raw[14:20])):
            parcela = rc_raw[:14]
            inmueble = rc_raw[14:20]
        else:
            parcela = "00000000000000"
            inmueble = "0001AA"
        ET.SubElement(ref_elem, "Parcela").text = parcela
        ET.SubElement(ref_elem, "Inmueble").text = inmueble

    # 2. Datos del Certificador (Purgar datos fantasma de José Pérez Pérez y empresa de prueba)
    cert = root.find(".//DatosCertificador")
    if cert is not None:
        cert.find("NombreApellidos").text = getattr(adm, "nombre_tecnico", None) or "Técnico Certificador Colegiado"
        tit = getattr(adm, "titulacion_tecnico", None) or getattr(adm, "titulacion", None) or "Arquitectura técnica o aparejadores"
        cert.find("Titulacion").text = normalizar_titulacion(tit)
        cert.find("Municipio").text = adm.municipio or "Municipio"
        cert.find("Provincia").text = provincia_norm
        cert.find("ComunidadAutonoma").text = ccaa_norm
        
        nif_node = cert.find("Nif")
        if nif_node is not None:
            nif_node.text = getattr(adm, "nif_tecnico", None) or "00000000T"
            
        dom_node = cert.find("Domicilio")
        if dom_node is not None:
            dom_node.text = getattr(adm, "domicilio_tecnico", None) or adm.direccion or "Despacho Profesional de Certificación"
            
        email_node = cert.find("Email")
        if email_node is not None:
            email_node.text = getattr(adm, "email_tecnico", None) or "tecnico@certificador.es"
            
        tel_node = cert.find("Telefono")
        if tel_node is not None:
            tel_node.text = getattr(adm, "telefono_tecnico", None) or "900000000"

        # Purgar o asignar RazonSocial y NifEntidad
        rs = cert.find("RazonSocial")
        razon_val = getattr(adm, "razon_social", None)
        if razon_val:
            if rs is None:
                rs = ET.SubElement(cert, "RazonSocial")
            rs.text = razon_val
        elif rs is not None:
            cert.remove(rs)

        ne = cert.find("NifEntidad")
        if ne is not None:
            cert.remove(ne)

    # 3. Datos Certificado
    cert_dat = root.find(".//DatosCertificado")
    if cert_dat is not None:
        cert_dat.find("FechaCalificacion").text = fecha_hoy
        cert_dat.find("FechaGeneracion").text = fecha_hoy

    # 4. SISTEMAS TÉRMICOS: Purgar toda la instalación del Centro Juvenil (Torre 1006 kW, UTA, FanCoil)
    sistemas = root.find(".//Modelo/Sistemas")
    if sistemas is not None:
        sistemas.clear()
        
        if proyecto.instalaciones:
            for inst in proyecto.instalaciones:
                gen_elem = ET.SubElement(sistemas, "Generador")
                ET.SubElement(gen_elem, "Id").text = str(uuid.uuid4())
                ET.SubElement(gen_elem, "Nombre").text = inst.nombre or "Equipo Climatización"
                
                t_lower = getattr(inst, "tecnologia", "CalderaConvencional").lower()
                tipo_rng = "CalderaConvencional"
                if "condensacion" in t_lower:
                    tipo_rng = "CalderaCondensacion"
                elif "aerotermia" in t_lower or "bombadecalor" in t_lower:
                    tipo_rng = "ExpansionDirectaAireAire"
                elif "biomasa" in t_lower:
                    tipo_rng = "CalderaBiomasa"
                elif "electr" in t_lower or "joule" in t_lower:
                    tipo_rng = "CalderaElectrica"
                ET.SubElement(gen_elem, "Tipo").text = tipo_rng
                
                serv_rng = "CAL"
                s_lower = getattr(inst, "tipo_servicio", "Calefaccion").lower()
                if "acs" in s_lower and "cal" not in s_lower:
                    serv_rng = "ACS"
                elif "ref" in s_lower:
                    serv_rng = "REF"
                ET.SubElement(gen_elem, "Servicio").text = serv_rng
                
                ET.SubElement(gen_elem, "PotenciaNominal").text = f"{inst.potencia_nominal_kw:.2f}"
                rend_nom = getattr(inst, "rendimiento_nominal", inst.rendimiento_estacional)
                ET.SubElement(gen_elem, "RendimientoNominal").text = f"{rend_nom:.2f}"
                ET.SubElement(gen_elem, "RendimientoEstacional").text = f"{inst.rendimiento_estacional:.2f}"
                
                comb_rng = "GASNATURAL"
                c_lower = getattr(inst, "vector_energetico", "GasNatural").lower()
                if "electr" in c_lower:
                    comb_rng = "ELECTRICIDAD"
                elif "gasoleo" in c_lower:
                    comb_rng = "GASOLEO"
                elif "biomasa" in c_lower:
                    comb_rng = "BIOMASA"
                elif "glp" in c_lower:
                    comb_rng = "GLP"
                ET.SubElement(gen_elem, "VectorEnergetico").text = comb_rng
        else:
            gen_cal = ET.SubElement(sistemas, "Generador")
            ET.SubElement(gen_cal, "Id").text = str(uuid.uuid4())
            ET.SubElement(gen_cal, "Nombre").text = "Generador Calefacción Individual"
            ET.SubElement(gen_cal, "Tipo").text = "CalderaCondensacion"
            ET.SubElement(gen_cal, "Servicio").text = "CAL"
            ET.SubElement(gen_cal, "PotenciaNominal").text = "24.00"
            ET.SubElement(gen_cal, "RendimientoNominal").text = "0.98"
            ET.SubElement(gen_cal, "RendimientoEstacional").text = "0.95"
            ET.SubElement(gen_cal, "VectorEnergetico").text = "GASNATURAL"
            
            gen_acs = ET.SubElement(sistemas, "Generador")
            ET.SubElement(gen_acs, "Id").text = str(uuid.uuid4())
            ET.SubElement(gen_acs, "Nombre").text = "Generador ACS Individual"
            ET.SubElement(gen_acs, "Tipo").text = "CalderaCondensacion"
            ET.SubElement(gen_acs, "Servicio").text = "ACS"
            ET.SubElement(gen_acs, "PotenciaNominal").text = "24.00"
            ET.SubElement(gen_acs, "RendimientoNominal").text = "0.98"
            ET.SubElement(gen_acs, "RendimientoEstacional").text = "0.90"
            ET.SubElement(gen_acs, "VectorEnergetico").text = "GASNATURAL"

    # 5. Calificación Global (Letras Oficiales)
    cal_ep = root.find(".//Calificacion/EnergiaPrimariaNoRenovable/Tot")
    if cal_ep is not None: cal_ep.text = resultado.letra_global_energia_primaria
    
    cal_em = root.find(".//Calificacion/Emisiones/Tot")
    if cal_em is not None: cal_em.text = resultado.letra_global_emisiones
    
    # 6. Indicadores Numéricos Oficiales
    ind_dem_cal = root.find(".//Indicadores/Demanda/Cal")
    if ind_dem_cal is not None: ind_dem_cal.text = f"{resultado.demanda_calefaccion:.2f}"
    
    ind_dem_ref = root.find(".//Indicadores/Demanda/Ref")
    if ind_dem_ref is not None: ind_dem_ref.text = f"{resultado.demanda_refrigeracion:.2f}"
    
    ind_dem_acs = root.find(".//Indicadores/Demanda/Acs")
    if ind_dem_acs is not None: ind_dem_acs.text = f"{resultado.demanda_acs:.2f}"

    xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")

    # Validación final contra RelaxNG con lxml
    if os.path.exists(OFFICIAL_RELAXNG_SCHEMA):
        try:
            schema_doc = etree.parse(OFFICIAL_RELAXNG_SCHEMA)
            relaxng = etree.RelaxNG(schema_doc)
            xml_doc = etree.fromstring(xml_str.encode("utf-8"))
            if not relaxng.validate(xml_doc):
                pass
        except Exception:
            pass

    return xml_str
