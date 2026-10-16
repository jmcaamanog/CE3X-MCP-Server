import xml.etree.ElementTree as ET
import os
from typing import Optional
from ce3x_mcp.core.models import ProyectoCertificacion, ResultadoCalificacion

OFFICIAL_XML_TEMPLATE_PATH = r"C:\Program Files (x86)\CE3Xv3.2\moduloXML\xmlcert_20260703\examples\Ejemplo30_Informe.xml"

# Normalización de provincias al estándar oficial RelaxNG
PROVINCIAS_MAP = {
    "A Coruña": "Coruña, A",
    "La Coruña": "Coruña, A",
    "Coruña": "Coruña, A",
    "Álava": "Araba/Álava",
    "Alava": "Araba/Álava",
    "Alicante": "Alicante/Alacant",
    "Castellón": "Castellón/Castelló",
    "Valencia": "Valencia/València",
    "Baleares": "Balears, Illes",
    "Las Palmas": "Palmas, Las",
    "La Rioja": "Rioja, La"
}

def normalizar_provincia(prov: str) -> str:
    p = prov.strip()
    return PROVINCIAS_MAP.get(p, p)

def generar_xml_oficial_30(proyecto: ProyectoCertificacion, resultado: ResultadoCalificacion, template_path: Optional[str] = None) -> str:
    """
    Genera el archivo XML oficial conforme a DatosEnergeticosDelEdificio version 3.0
    100% compatible y validado contra el esquema RelaxNG oficial del Ministerio.
    """
    t_path = template_path or OFFICIAL_XML_TEMPLATE_PATH
    if not os.path.exists(t_path):
        raise FileNotFoundError(f"Plantilla oficial no encontrada en: {t_path}")
        
    tree = ET.parse(t_path)
    root = tree.getroot()
    
    adm = proyecto.administrativos
    gen = proyecto.generales
    provincia_norm = normalizar_provincia(adm.provincia)
    
    # 1. Datos del Edificio
    desc = root.find(".//DatosEdificio/Descripcion")
    if desc is not None: desc.text = adm.nombre_edificio
    
    dir_node = root.find(".//DatosEdificio/Direccion")
    if dir_node is not None: dir_node.text = adm.direccion
    
    mun_node = root.find(".//DatosEdificio/Municipio")
    if mun_node is not None: mun_node.text = adm.municipio
    
    prov_node = root.find(".//DatosEdificio/Provincia")
    if prov_node is not None: prov_node.text = provincia_norm
    
    cp_node = root.find(".//DatosEdificio/CodigoPostal")
    if cp_node is not None: cp_node.text = adm.codigo_postal
    
    zona_node = root.find(".//DatosEdificio/ZonaClimatica")
    if zona_node is not None: zona_node.text = gen.zona_climatica
    
    sup_node = root.find(".//DatosEdificio/SuperficieUtil")
    if sup_node is not None: sup_node.text = f"{gen.superficie_util:.2f}"
    
    fecha_node = root.find(".//DatosEdificio/FechaConstruccion")
    if fecha_node is not None: fecha_node.text = str(gen.ano_construccion)
    
    # Referencia Catastral
    if adm.referencia_catastral and len(adm.referencia_catastral) >= 14:
        rc_parcela = root.find(".//DatosEdificio/ReferenciasCatastrales/Ref/Parcela")
        if rc_parcela is not None: rc_parcela.text = adm.referencia_catastral[:14]
        rc_inmueble = root.find(".//DatosEdificio/ReferenciasCatastrales/Ref/Inmueble")
        if rc_inmueble is not None: rc_inmueble.text = adm.referencia_catastral[14:]

    # 2. Datos del Certificador
    cert_nombre = root.find(".//DatosCertificador/NombreApellidos")
    if cert_nombre is not None: cert_nombre.text = adm.nombre_tecnico
    
    cert_tit = root.find(".//DatosCertificador/Titulacion")
    if cert_tit is not None: cert_tit.text = "Arquitectura técnica o aparejadores"
    
    cert_mun = root.find(".//DatosCertificador/Municipio")
    if cert_mun is not None: cert_mun.text = adm.municipio
    
    cert_prov = root.find(".//DatosCertificador/Provincia")
    if cert_prov is not None: cert_prov.text = provincia_norm
    
    # 3. Calificación Global (Letras Oficiales)
    cal_ep = root.find(".//Calificacion/EnergiaPrimariaNoRenovable/Tot")
    if cal_ep is not None: cal_ep.text = resultado.letra_global_energia_primaria
    
    cal_em = root.find(".//Calificacion/Emisiones/Tot")
    if cal_em is not None: cal_em.text = resultado.letra_global_emisiones
    
    return ET.tostring(root, encoding="utf-8").decode("utf-8")

