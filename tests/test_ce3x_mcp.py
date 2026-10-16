import sys
import os

sys.path.insert(0, r"C:\Users\Jose\OneDrive\GITHUB\CE3X-MCP-Server\src")

from ce3x_mcp.services.cte_climate import obtener_zona_climatica, estimar_transmitancias_por_ano
from ce3x_mcp.core.models import ProyectoCertificacion, DatosAdministrativos, DatosGenerales, ResultadoCalificacion
from ce3x_mcp.services.xml_builder import generar_xml_oficial_30
from ce3x_mcp.services.cex_codec import guardar_fichero_cex_basico, leer_fichero_cex
from ce3x_mcp.services.equipment_parser import analizar_datos_equipo_climatizacion
from ce3x_mcp.services.improvement_engine import calcular_paquetes_medidas_mejora
import tempfile

def test_cte_climate():
    assert obtener_zona_climatica("A Coruña", "A Coruña") == "C1"
    assert obtener_zona_climatica("Madrid", "Madrid") == "D3"
    t1970 = estimar_transmitancias_por_ano(1970, "C1")
    assert t1970["normativa"] == "Anterior1979"
    assert t1970["u_fachada"] == 1.80
    print("[PASS] test_cte_climate")

def test_xml_generation():
    adm = DatosAdministrativos(
        nombre_edificio="Vivienda Test",
        direccion="Rúa Real 1",
        municipio="A Coruña",
        provincia="A Coruña",
        codigo_postal="15001"
    )
    gen = DatosGenerales(
        ano_construccion=1990,
        zona_climatica="C1",
        superficie_util=85.0
    )
    res = ResultadoCalificacion(
        demanda_calefaccion=45.0,
        demanda_refrigeracion=12.0,
        demanda_acs=20.0,
        consumo_energia_primaria_nr=85.0,
        emisiones_co2=22.0,
        letra_global_emisiones="E",
        letra_global_energia_primaria="E",
        letra_calefaccion="E",
        letra_refrigeracion="A",
        letra_acs="E"
    )
    proy = ProyectoCertificacion(administrativos=adm, generales=gen)
    xml_str = generar_xml_oficial_30(proy, res)
    assert "<DatosEnergeticosDelEdificio" in xml_str
    print("[PASS] test_xml_generation")

def test_equipment_parser():
    res1 = analizar_datos_equipo_climatizacion("Bomba de calor aerotermia Daikin Altherma de 11 kW con SCOP de 3.65 para calefacción y ACS")
    assert res1["tecnologia_detectada"] == "BombaCalorAerotermia"
    assert res1["potencia_nominal_kw"] == 11.0
    assert res1["rendimiento_estacional"] == 3.65
    
    res2 = analizar_datos_equipo_climatizacion("Caldera de condensación Saunier Duval Thelia Condens de 25 kW a gas natural")
    assert res2["tecnologia_detectada"] == "CalderaCondensacion"
    assert res2["potencia_nominal_kw"] == 25.0
    print("[PASS] test_equipment_parser")

def test_improvement_engine():
    adm = DatosAdministrativos(nombre_edificio="Edif", direccion="Dir", municipio="A Coruña", provincia="A Coruña", codigo_postal="15001")
    gen = DatosGenerales(ano_construccion=1975, zona_climatica="C1", superficie_util=90.0)
    proy = ProyectoCertificacion(administrativos=adm, generales=gen)
    act = ResultadoCalificacion(
        demanda_calefaccion=65.0,
        demanda_refrigeracion=15.0,
        demanda_acs=22.0,
        consumo_energia_primaria_nr=120.0,
        emisiones_co2=35.0,
        letra_global_emisiones="E",
        letra_global_energia_primaria="E",
        letra_calefaccion="E",
        letra_refrigeracion="A",
        letra_acs="E"
    )
    medidas = calcular_paquetes_medidas_mejora(proy, act)
    assert len(medidas) == 3
    assert medidas[0].tipo == "Envolvente"
    assert medidas[1].tipo == "Instalaciones"
    assert medidas[2].tipo == "Conjunto"
    assert medidas[2].nueva_letra_emisiones == "A"
    print("[PASS] test_improvement_engine")

if __name__ == "__main__":
    test_cte_climate()
    test_xml_generation()
    test_equipment_parser()
    test_improvement_engine()
    print("\nTODOS LOS TESTS (INCLUYENDO MULTIMODAL Y MEJORAS) HAN PASADO EXITOSAMENTE!")


