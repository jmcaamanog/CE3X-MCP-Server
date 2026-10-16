import sys
import os

sys.path.insert(0, r"C:\Users\Jose\OneDrive\GITHUB\CE3X-MCP-Server\src")

from ce3x_mcp.services.cte_climate import obtener_zona_climatica, estimar_transmitancias_por_ano
from ce3x_mcp.core.models import ProyectoCertificacion, DatosAdministrativos, DatosGenerales, ResultadoCalificacion
from ce3x_mcp.services.xml_builder import generar_xml_oficial_30
from ce3x_mcp.services.cex_codec import guardar_fichero_cex_basico, leer_fichero_cex
from ce3x_mcp.services.equipment_parser import analizar_datos_equipo_climatizacion
from ce3x_mcp.services.improvement_engine import calcular_paquetes_medidas_mejora
from ce3x_mcp.services.pvgis_client import calcular_produccion_solar_pvgis
from ce3x_mcp.services.smart_folder_auditor import auditar_carpeta_inmueble, certificar_inmueble_desde_carpeta, organizar_carpeta_visita
from ce3x_mcp.services.libraries import inferir_solucion_envolvente_por_ano, CATALOGO_VIDRIOS
from ce3x_mcp.services.nextgen_report import generar_informe_justificativo_nextgen
from ce3x_mcp.services.plan_parser import analizar_plano_distribucion_pdf
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
    print("[PASS] test_equipment_parser")

def test_improvement_engine_and_nextgen():
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
    
    # Test NextGen report
    dictamen = generar_informe_justificativo_nextgen(proy, act, medidas[2])
    assert dictamen["valido"] is True
    assert dictamen["cumple_umbral_nextgen_30"] is True
    assert dictamen["porcentaje_ahorro_epnr"] >= 30.0
    assert "Dictamen Técnico Justificativo" in dictamen["dictamen_markdown"]
    print("[PASS] test_improvement_engine_and_nextgen")

def test_pvgis():
    res = calcular_produccion_solar_pvgis(43.36, -8.41, 3.0)
    assert res["valido"] is True
    assert res["produccion_anual_kwh"] > 2000.0
    print("[PASS] test_pvgis")


def test_libraries():
    sol_1982 = inferir_solucion_envolvente_por_ano(1982, "Galicia")
    assert sol_1982["fachada_recomendada"]["periodo"] == "1980-2006"
    assert "simple" in inferir_solucion_envolvente_por_ano(1975)["vidrio_recomendado"]["nombre"].lower()
    print("[PASS] test_libraries")

def test_smart_folder_auditor():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 1. Crear archivos sueltos desordenados en raíz
        with open(os.path.join(tmp_dir, "apuntes_visita.txt"), "w", encoding="utf-8") as fp:
            fp.write(
                "Visita al inmueble:\n"
                "Referencia Catastral: 2344201XK3724S0001LD\n"
                "Agua caliente sanitaria mediante termo electrico de 80 litros.\n"
                "Carpinteria de aluminio blanco sin persianas en salon.\n"
            )
        with open(os.path.join(tmp_dir, "plano_distribucion_vivienda.pdf"), "w", encoding="utf-8") as fp:
            fp.write("%PDF-1.4 simulacion plano")
        with open(os.path.join(tmp_dir, "foto_fachada_principal.jpg"), "w", encoding="utf-8") as fp:
            fp.write("simulacion imagen fachada")
        with open(os.path.join(tmp_dir, "placa_caldera_gas_natural_condensacion.jpg"), "w", encoding="utf-8") as fp:
            fp.write("simulacion placa caldera")

        # 2. Test organizar_carpeta_visita
        org_res = organizar_carpeta_visita(tmp_dir)
        assert org_res["estado"] == "organizado_exitoso"
        assert org_res["total_archivos_movidos"] == 4
        assert os.path.exists(os.path.join(tmp_dir, "INFORMACION", "apuntes_visita.txt"))
        assert os.path.exists(os.path.join(tmp_dir, "PLANOS", "plano_distribucion_vivienda.pdf"))
        assert os.path.exists(os.path.join(tmp_dir, "FOTOS", "foto_fachada_principal.jpg"))
        assert os.path.exists(os.path.join(tmp_dir, "INSTALACIONES", "placa_caldera_gas_natural_condensacion.jpg"))
        assert os.path.exists(os.path.join(tmp_dir, "CERTIFICADO"))
        assert os.path.exists(os.path.join(tmp_dir, "LEEME_ESTRUCTURA_VISITA.txt"))

        # 3. Test auditar_carpeta_inmueble tras organizar
        res = auditar_carpeta_inmueble(tmp_dir)
        assert res["estado"] == "auditado"
        assert res["carpeta_organizada"] is True
        assert res["referencia_catastral_encontrada"] == "2344201XK3724S0001LD"
        assert res["climatizacion_detectada"]["calefaccion"] == "CalderaCondensacion"
        assert len(res["preguntas_quirurgicas_al_tecnico"]) >= 1
        assert res["directorio_entrega_certificado"] == os.path.join(tmp_dir, "CERTIFICADO")

        # 4. Test generacion automatica en subcarpeta CERTIFICADO/
        cert_res = certificar_inmueble_desde_carpeta(tmp_dir)
        assert cert_res["estado"] == "completado_exitoso"
        cert_dir = os.path.join(tmp_dir, "CERTIFICADO")
        assert os.path.exists(cert_dir)
        assert os.path.exists(os.path.join(cert_dir, "Proyecto_CE3X.cex"))
        assert os.path.exists(os.path.join(cert_dir, "Certificado_Oficial_Registro.xml"))
        assert os.path.exists(os.path.join(cert_dir, "Informe_Certificacion_Energetica.pdf"))
        assert os.path.exists(os.path.join(cert_dir, "Informe_Medidas_Mejora_NextGen.md"))
        assert os.path.exists(os.path.join(cert_dir, "Informe_Medidas_Mejora_NextGen.pdf"))
        assert os.path.exists(os.path.join(cert_dir, "RESUMEN_ENTREGA.txt"))
        print("[PASS] test_smart_folder_auditor, organizar_carpeta_visita y entregables en CERTIFICADO/")


if __name__ == "__main__":
    test_libraries()
    test_smart_folder_auditor()
    test_cte_climate()
    test_xml_generation()
    test_equipment_parser()
    test_improvement_engine_and_nextgen()
    test_pvgis()
    print("\nTODOS LOS TESTS UNITARIOS Y DE INTEGRACIÓN HAN PASADO EXITOSAMENTE (100%)!")

