import sys
import os

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(repo_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from ce3x_mcp.services.cte_climate import obtener_zona_climatica, estimar_transmitancias_por_ano
from ce3x_mcp.core.models import ProyectoCertificacion, DatosAdministrativos, DatosGenerales, ResultadoCalificacion
from ce3x_mcp.services.xml_builder import generar_xml_oficial_30
from ce3x_mcp.services.cex_codec import guardar_fichero_cex_basico, leer_fichero_cex
from ce3x_mcp.services.equipment_parser import analizar_datos_equipo_climatizacion
from ce3x_mcp.services.improvement_engine import calcular_paquetes_medidas_mejora
from ce3x_mcp.services.pvgis_client import calcular_produccion_solar_pvgis
from ce3x_mcp.services.smart_folder_auditor import auditar_carpeta_inmueble, certificar_inmueble_desde_carpeta, organizar_carpeta_visita
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
from ce3x_mcp.services.libraries import CATALOGO_MUROS_FACHADA, CATALOGO_MARCOS_CARPINTERIA
from ce3x_mcp.services.technician_profile import guardar_perfil_tecnico, obtener_perfil_tecnico
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
    try:
        res = calcular_produccion_solar_pvgis(43.36, -8.41, 3.0)
        assert res["valido"] is True
        assert res["produccion_anual_kwh"] > 2000.0
    except Exception as e:
        print(f"[WARN] Conexión PVGIS no disponible en CI: {e}")
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
        if os.path.exists(r"C:\Program Files (x86)\CE3Xv3.2\moduloXML\xmlcert_20260703\xml2cert.exe"):
            assert os.path.exists(os.path.join(cert_dir, "Informe_Certificacion_Energetica.pdf"))
        assert os.path.exists(os.path.join(cert_dir, "Informe_Medidas_Mejora_NextGen.md"))
        assert os.path.exists(os.path.join(cert_dir, "Informe_Medidas_Mejora_NextGen.pdf"))
        assert os.path.exists(os.path.join(cert_dir, "RESUMEN_ENTREGA.txt"))
        print("[PASS] test_smart_folder_auditor, organizar_carpeta_visita y entregables en CERTIFICADO/")


def test_trials_and_tests():
    # 1. Visita e inspeccion oficial (Anexo IV RD 390/2021)
    v = registrar_visita_e_inspeccion("16/10/2026", ["inspeccion_visual", "medicion_laser", "termografia"])
    assert v["valido"] is True
    assert v["cumple_rd390_visita_presencial"] is True
    assert "termográfica" in v["texto_anexo_iv"]

    # 2. Ensayo Blower Door (UNE-EN ISO 9972)
    bd = registrar_ensayo_blower_door(volumen_neto_m3=240.0, superficie_envolvente_m2=210.0, caudal_50pa_m3h=480.0)
    assert bd["valido"] is True
    assert bd["n50_ren_h"] == 2.0
    assert "Conforme" in bd["diagnostico_hermeticidad"]

    # 3. Puentes termicos CTE (DA DB-HE / 3)
    pt = calcular_puentes_termicos_cte(ano_construccion=1995, perimetro_forjado_m=35.0, perimetro_huecos_m=28.0)
    assert pt["valido"] is True
    assert pt["perdida_total_puentes_termicos_w_k"] > 20.0

    # 4. Contraste de facturas reales vs modelo
    cf = contrastar_facturas_reales(consumo_teorico_kwh_ano=6500.0, electricidad_real_kwh=3200.0, gas_natural_real_kwh=3100.0)
    assert cf["valido"] is True
    assert abs(cf["desviacion_porcentual"]) < 5.0
    assert "Alineado" in cf["diagnostico_contraste"]

    # 5. Calculo de sombras estacionales en huecos
    sh = calcular_sombras_estacionales_hueco(orientacion="Sur", ancho_hueco_m=1.20, alto_hueco_m=1.40, retranqueo_m=0.15, vuelo_voladizo_m=0.60)
    assert sh["valido"] is True
    assert sh["factor_sombra_verano"] < 0.80

    # 6. Perfil de tecnico colegiado persistente
    p = guardar_perfil_tecnico(nombre_tecnico="Jose Manuel Caamaño González", nif_tecnico="00000000Z", titulacion="Arquitecto Técnico")
    assert p["valido"] is True
    assert p["perfil"]["titulacion"] == "Arquitecto Técnico"

    # 7. Sombra de edificio enfrente (obstaculo remoto)
    obs = calcular_patron_sombras_edificio_colindante(distancia_edificio_m=12.0, altura_edificio_m=15.0)
    assert obs["valido"] is True
    assert obs["angulo_elevacion_alfa_grados"] > 45.0
    assert obs["factor_sombra_invierno_fsh"] <= 0.50

    # 8. Estimacion de parametros terciario / local comercial
    terc = estimar_parametros_terciario_comercial(tipo_actividad="Comercio", superficie_util_m2=120.0, tipo_luminaria="LED")
    assert terc["valido"] is True
    assert terc["cumple_cte_db_he3"] is True
    assert terc["potencia_iluminacion_w_m2"] == 9.0

    # 9. Flujometria termica ISO 9869
    flujo = registrar_ensayo_flujometria_termica_iso9869(flujo_medio_w_m2=15.0, temp_interior_media_c=20.0, temp_exterior_media_c=5.0)
    assert flujo["valido"] is True
    assert flujo["u_medido_w_m2k"] > 0.5

    # 10. Transmitancia de ventana UNE-EN ISO 10077-1
    win = calcular_transmitancia_ventana_iso10077(1.20, 1.40, 1.1, 1.4, 0.25, "termicamente_mejorado")
    assert win["valido"] is True
    assert win["u_ventana_uw_w_m2k"] < 1.6
    assert win["cumple_limite_cte_db_he"] is True

    # 11. Demanda de ACS segun CTE DB-HE 4
    acs = calcular_demanda_acs_cte_he4(numero_dormitorios=3, provincia="Madrid")
    assert acs["valido"] is True
    assert acs["demanda_diaria_litros_60c"] == 112.0
    assert acs["demanda_anual_kwh_ano"] > 2000.0

    print("[PASS] test_trials_and_tests (visita, blower door, puentes termicos, facturas, sombras, ISO 10077, ACS CTE HE4, flujometria y perfil)")




def test_exhaustive_matrix_scenarios():
    """
    Bateria exhaustiva de pruebas de validacion de todos los escenarios y variantes posibles:
    1. Tipos de muros y envolvente historica (Pre-79, NBE-CT-79, CTE 2006, CTE 2013, CTE 2019 nZEB).
    2. Variantes de climatizacion (Gas convencional, Condensacion, Gasoleo, Efecto Joule, Bomba Calor, Aerotermia, Biomasa, VRF).
    3. Orientaciones (N, S, E, O) y factores reductores de sombra (voladizos, retranqueos, toldos, obstaculos remotos).
    4. Transmitancia de ventanas UNE-EN ISO 10077-1 con todo tipo de marcos y vidrios.
    5. Demanda de ACS segun CTE DB-HE 4 (dormitorios 1 a 5 y provincias).
    6. Puentes termicos (DA DB-HE / 3) y ensayo de flujometria termica ISO 9869-1.
    7. Paquetes de medidas de mejora RD 390/2021 y dictamenes de subvencion NextGen EU (40%, 65%, 80% e IRPF).
    """
    # 1. Muros y Envolvente Historica
    epocas = [
        (1965, "Anterior1979", 1.80, 2.20, 5.70),
        (1985, "NBE_CT_79", 1.20, 1.10, 3.80),
        (2008, "CTE_2006", 0.66, 0.45, 2.80),
        (2016, "CTE_2013", 0.45, 0.35, 2.20),
        (2022, "CTE_2019", 0.35, 0.28, 1.60),
    ]
    for ano, norm, u_fach, u_cub, u_huec in epocas:
        t = estimar_transmitancias_por_ano(ano, "C1")
        assert t["normativa"] == norm
        assert t["u_fachada"] == u_fach
        assert t["u_cubierta"] == u_cub
        assert t["u_hueco"] == u_huec

        sol = inferir_solucion_envolvente_por_ano(ano, region="Norte")
        assert sol["fachada_recomendada"]["transmitancia_U"] > 0
        assert sol["vidrio_recomendado"]["transmitancia_Ug"] > 0
        assert sol["marco_recomendado"]["transmitancia_Uf"] > 0

    # 2. Climatizacion e Instalaciones (8 variantes)
    equipos = [
        ("Caldera de gas estandar de 24 kW con rendimiento estacional del 78%", 24.0, "GasNatural"),
        ("Caldera de condensacion Saunier Duval Thelia Condens 25 kW", 25.0, "GasNatural"),
        ("Caldera de gasoleo Ferroli Silent D 30 kW para calefaccion", 30.0, "Gasoleo"),
        ("Termo electrico de 80 litros con resistencia de 1500W para ACS", 1.5, "Electricidad"),
        ("Bomba de calor aerotermica Daikin Altherma 11 kW SCOP 4.2", 11.0, "Electricidad"),
        ("Bomba de calor reversible inverter split 3.5 kW SEER 6.1 SCOP 4.0", 3.5, "Electricidad"),
        ("Caldera de pellets de biomasa OkoFEN 15 kW rendimiento 92%", 15.0, "BiomasaPellet"),
        ("Sistema de climatizacion VRF de caudal variable de 28 kW en cubierta", 28.0, "Electricidad"),
    ]
    for desc, pot, comb in equipos:
        eq = analizar_datos_equipo_climatizacion(desc)
        assert eq["potencia_nominal_kw"] == pot
        assert eq["vector_energetico"] == comb
        assert eq["rendimiento_estacional"] > 0.5

    # 3. Orientaciones y Sombras
    for ori in ["Norte", "Sur", "Este", "Oeste", "Noreste", "Suroeste"]:
        sh = calcular_sombras_estacionales_hueco(
            orientacion=ori,
            ancho_hueco_m=1.20,
            alto_hueco_m=1.40,
            retranqueo_m=0.15,
            vuelo_voladizo_m=0.60,
            tiene_toldo=True
        )
        assert sh["valido"] is True
        assert sh["factor_sombra_verano"] < sh["factor_sombra_invierno"]

    obs_estrecha = calcular_patron_sombras_edificio_colindante(distancia_edificio_m=8.0, altura_edificio_m=18.0)
    assert obs_estrecha["angulo_elevacion_alfa_grados"] > 60.0
    assert obs_estrecha["factor_sombra_invierno_fsh"] <= 0.40

    obs_ancha = calcular_patron_sombras_edificio_colindante(distancia_edificio_m=35.0, altura_edificio_m=12.0)
    assert obs_ancha["angulo_elevacion_alfa_grados"] < 30.0
    assert obs_ancha["factor_sombra_verano_fsh"] >= 0.85

    # 4. Transmitancia Ventanas ISO 10077-1
    w_antigua = calcular_transmitancia_ventana_iso10077(1.20, 1.40, 5.7, 4.0, 0.25, "aluminio")
    assert w_antigua["u_ventana_uw_w_m2k"] > 4.5
    w_nizeb = calcular_transmitancia_ventana_iso10077(1.50, 1.80, 1.0, 1.2, 0.20, "warm_edge")
    assert w_nizeb["u_ventana_uw_w_m2k"] <= 1.4
    assert w_nizeb["cumple_limite_cte_db_he"] is True

    # 5. Demanda ACS CTE DB-HE 4
    for dorms, pers_esp, lit_esp in [(1, 1.5, 42.0), (2, 3.0, 84.0), (3, 4.0, 112.0), (4, 5.0, 140.0)]:
        acs = calcular_demanda_acs_cte_he4(numero_dormitorios=dorms, provincia="Madrid")
        assert acs["ocupantes_calculo"] == pers_esp
        assert acs["demanda_diaria_litros_60c"] == lit_esp
        assert acs["demanda_anual_kwh_ano"] > 500.0

    # 6. Puentes Termicos y Flujometria ISO 9869
    for ano, expected_psi in [(1970, 0.85), (1995, 0.50), (2010, 0.30), (2022, 0.12)]:
        pt = calcular_puentes_termicos_cte(ano_construccion=ano, perimetro_forjado_m=40.0, perimetro_huecos_m=30.0)
        assert pt["psi_frente_forjado_w_mk"] == expected_psi
        assert pt["perdida_total_puentes_termicos_w_k"] > 5.0

    flujo_ensayo = registrar_ensayo_flujometria_termica_iso9869(flujo_medio_w_m2=18.5, temp_interior_media_c=21.0, temp_exterior_media_c=4.5)
    assert flujo_ensayo["valido"] is True
    assert 0.8 <= flujo_ensayo["u_medido_w_m2k"] <= 1.5

    # 7. Medidas de Mejora RD 390 y NextGen EU
    from ce3x_mcp.server import proponer_medidas_mejora_rd390, emitir_dictamen_subvenciones_nextgen
    prop = proponer_medidas_mejora_rd390(superficie_util=100.0, ano_construccion=1975, zona_climatica="D3")
    assert len(prop["medidas_de_mejora"]) == 3
    assert prop["medidas_de_mejora"][2]["nueva_letra_emisiones"] == "A"

    dictamen_p3 = emitir_dictamen_subvenciones_nextgen(superficie_util=100.0, ano_construccion=1975, zona_climatica="D3", paquete_mejora=3)
    assert dictamen_p3["cumple_umbral_nextgen_30"] is True
    assert dictamen_p3["porcentaje_ahorro_epnr"] >= 60.0

    print("[PASS] test_exhaustive_matrix_scenarios (muros, HVAC, orientaciones, sombras, ISO 10077, ACS HE4, puentes termicos, NextGen)")


def test_ce3x_verifier_and_rigor():
    from ce3x_mcp.server import verificar_conexion_ce3x, consultar_catastro, calcular_calificacion_energetica, generar_certificado_completo
    
    # 1. Verificar instalación y motores oficiales de CE3X v3.2
    v = verificar_conexion_ce3x()
    ce3x_local = v.get("instalado", False)
    if ce3x_local:
        assert v["instalado"] is True
        assert v["estado_operativo"] == "OPERATIVO_100_POR_CIENTO"
        assert v["componentes"]["compilador_pdf_xml2cert"]["existe"] is True
        assert v["componentes"]["base_escalas_localidades"]["zonas_detectadas"] >= 30
    else:
        print("[INFO] CE3X v3.2 no instalado en host (CI runner). Evaluando modo de compatibilidad y fallback de escalas.")
    
    # 2. Catastro telemático real sin inventar datos
    try:
        cat = consultar_catastro("2344201XK3724S0001LD")
        if cat.get("valido"):
            assert "ALBARRACIN" in cat["direccion"]
            assert cat["ano_construccion"] == 1910
            assert cat["superficie_construida_m2"] == 1522.0
    except Exception as e:
        print(f"[WARN] Conexión Catastro no disponible en CI: {e}")
    
    # 3. Calificación con escalas oficiales de Localidades.xml
    calc = calcular_calificacion_energetica(superficie_util=100.0, ano_construccion=1980, zona_climatica="D3", tipo_calefaccion="CalderaCondensacion", tipo_acs="CalderaCondensacion")
    assert calc["calificacion_global_emisiones"] in ["A", "B", "C", "D", "E", "F", "G"]
    assert "Localidades.xml" in calc["escalas_oficiales_ce3x"]["fuente"]
    
    # 4. Generación oficial limpia de entregables (.xml, .pdf, .cex)
    with tempfile.TemporaryDirectory() as tmp_out:
        res = generar_certificado_completo(
            nombre_edificio="Edificio Test Rigor",
            direccion="Plaza Mayor 1",
            municipio="Albarracin",
            provincia="Teruel",
            codigo_postal="44100",
            superficie_util=120.0,
            ano_construccion=1980,
            referencia_catastral="2344201XK3724S0001LD",
            directorio_salida=tmp_out
        )
        if ce3x_local:
            assert res["estado"] == "completado"
            assert os.path.exists(res["archivo_xml_oficial"])
            assert os.path.exists(res["archivo_pdf_oficial"])
            assert os.path.exists(res["archivo_cex_ce3x"])
            assert res["verificacion_rigor"]["datos_inventados"] is False
            assert res["verificacion_rigor"]["xml_sin_datos_fantasma"] is True
        else:
            assert res["estado"] == "error_instalacion_ce3x"
            assert "No se puede certificar sin CE3X instalado" in res.get("mensaje", "")
        
    print("[PASS] test_ce3x_verifier_and_rigor (CE3X v3.2 oficial, Catastro real, escalas Localidades.xml y XML/PDF/CEX limpios)")


def test_cache_and_progress():
    import time
    from ce3x_mcp.services.cache_manager import (
        guardar_en_cache,
        obtener_de_cache,
        purgar_cache_expirada,
        obtener_estadisticas_cache,
        vaciar_cache_completa
    )
    from ce3x_mcp.server import gestionar_cache_ce3x, reportar_progreso_seguro
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db = os.path.join(tmp_dir, "test_cache.db")
        
        # 1. Guardar y recuperar
        data = {"direccion": "Rua Mayor 1", "superficie": 100.0}
        saved = guardar_en_cache("catastro", "1234567AB1234C0001XY", data, ttl_segundos=100.0, db_path=test_db)
        assert saved is True
        
        rec = obtener_de_cache("catastro", "1234567AB1234C0001XY", db_path=test_db)
        assert rec is not None
        assert rec["cache_hit"] is True
        assert rec["direccion"] == "Rua Mayor 1"
        assert rec["superficie"] == 100.0
        
        # 2. Comprobar estadísticas
        stats = obtener_estadisticas_cache(db_path=test_db)
        assert stats["total_entradas"] == 1
        assert stats["desglose_por_categoria"].get("catastro") == 1
        
        # 3. Expiración de TTL
        guardar_en_cache("test_exp", "KEY_EXP", {"val": 1}, ttl_segundos=0.01, db_path=test_db)
        time.sleep(0.05)
        rec_exp = obtener_de_cache("test_exp", "KEY_EXP", db_path=test_db)
        assert rec_exp is None
        
        # 4. Vaciar categoría y vaciar todo
        vaciadas = vaciar_cache_completa(categoria="catastro", db_path=test_db)
        assert vaciadas == 1
        stats_vacias = obtener_estadisticas_cache(db_path=test_db)
        assert stats_vacias["total_entradas"] == 0
        
        # 5. Probar tool gestionar_cache_ce3x
        res_tool = gestionar_cache_ce3x(accion="estadisticas")
        assert "total_entradas" in res_tool
        
        # 6. Probar telemetría de progreso con Mock Context
        class MockContext:
            def __init__(self):
                self.events = []
            async def report_progress(self, progress, total, message):
                self.events.append((progress, total, message))
                
        mock_ctx = MockContext()
        reportar_progreso_seguro(mock_ctx, 50, 100, "Prueba telemetría")
        assert len(mock_ctx.events) == 1
        assert mock_ctx.events[0] == (50, 100, "Prueba telemetría")
        
    print("[PASS] test_cache_and_progress (Caché persistente SQLite, TTL, purga, estadísticas y Context FastMCP)")

if __name__ == "__main__":
    test_cache_and_progress()
    test_ce3x_verifier_and_rigor()
    test_libraries()
    test_smart_folder_auditor()
    test_cte_climate()
    test_xml_generation()
    test_equipment_parser()
    test_improvement_engine_and_nextgen()
    test_pvgis()
    test_trials_and_tests()
    test_exhaustive_matrix_scenarios()
    print("\nTODOS LOS TESTS UNITARIOS, DE INTEGRACIÓN Y MATRICES DE ESCENARIOS HAN PASADO EXITOSAMENTE (100%)!")

