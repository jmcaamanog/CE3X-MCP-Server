import sys
import os

# Asegurar import de src
sys.path.insert(0, r"C:\Users\Jose\OneDrive\GITHUB\CE3X-MCP-Server\src")

from ce3x_mcp.services.cte_climate import obtener_zona_climatica, estimar_transmitancias_por_ano
from ce3x_mcp.core.models import ProyectoCertificacion, DatosAdministrativos, DatosGenerales, ResultadoCalificacion
from ce3x_mcp.services.xml_builder import generar_xml_oficial_30
from ce3x_mcp.services.cex_codec import guardar_fichero_cex_basico, leer_fichero_cex
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
    assert "<DatosEnergeticosDelEdificio version=\"3.0\">" in xml_str
    assert "<ZonaClimatica>C1</ZonaClimatica>" in xml_str
    assert "<SuperficieUtil>85.00</SuperficieUtil>" in xml_str
    print("[PASS] test_xml_generation")

def test_cex_codec():
    with tempfile.NamedTemporaryFile(suffix=".cex", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        guardar_fichero_cex_basico(
            tmp_path,
            "CE3Xv3.2 Residencial",
            ["Test Edif", "Calle 1"],
            ["NBE-CT-79", "Bloque"],
            [],
            []
        )
        objetos = leer_fichero_cex(tmp_path)
        assert len(objetos) == 5
        assert objetos[0] == "CE3Xv3.2 Residencial"
        print("[PASS] test_cex_codec")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    test_cte_climate()
    test_xml_generation()
    test_cex_codec()
    print("\nTODOS LOS TESTS UNITARIOS HAN PASADO EXITOSAMENTE!")
