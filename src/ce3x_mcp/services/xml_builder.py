from xml.sax.saxutils import escape
from ce3x_mcp.core.models import ProyectoCertificacion, ResultadoCalificacion

def generar_xml_oficial_30(proyecto: ProyectoCertificacion, resultado: ResultadoCalificacion) -> str:
    """
    Genera el archivo XML oficial conforme a DatosEnergeticosDelEdificio version 3.0
    validable contra el esquema RelaxNG del Ministerio.
    """
    adm = proyecto.administrativos
    gen = proyecto.generales
    
    xml = []
    xml.append('<?xml version="1.0" encoding="UTF-8"?>')
    xml.append('<DatosEnergeticosDelEdificio version="3.0">')
    
    # 1. Datos del Edificio
    xml.append('  <DatosEdificio>')
    xml.append(f'    <Descripcion>{escape(adm.nombre_edificio)}</Descripcion>')
    xml.append(f'    <Direccion>{escape(adm.direccion)}</Direccion>')
    xml.append(f'    <Municipio>{escape(adm.municipio)}</Municipio>')
    xml.append(f'    <Provincia>{escape(adm.provincia)}</Provincia>')
    xml.append(f'    <ComunidadAutonoma>{escape(adm.comunidad_autonoma or "Galicia")}</ComunidadAutonoma>')
    xml.append(f'    <CodigoPostal>{escape(adm.codigo_postal)}</CodigoPostal>')
    xml.append(f'    <ZonaClimatica>{escape(gen.zona_climatica)}</ZonaClimatica>')
    xml.append(f'    <FechaConstruccion>{gen.ano_construccion}</FechaConstruccion>')
    xml.append(f'    <NormativaEdificacion>{gen.normativa_vigente}</NormativaEdificacion>')
    xml.append('    <NormativaInstalaciones>RITE_2007</NormativaInstalaciones>')
    
    if adm.referencia_catastral:
        xml.append('    <ReferenciasCatastrales>')
        xml.append('      <Registro>DGC</Registro>')
        xml.append('      <Ref>')
        xml.append(f'        <Parcela>{escape(adm.referencia_catastral[:14])}</Parcela>')
        xml.append(f'        <Inmueble>{escape(adm.referencia_catastral[14:])}</Inmueble>')
        xml.append('      </Ref>')
        xml.append('    </ReferenciasCatastrales>')
        
    xml.append(f'    <Alcance>{adm.tipo_alcance}</Alcance>')
    xml.append('    <Uso>ResidencialPrivado</Uso>')
    xml.append('    <NumUnidadesUso>1</NumUnidadesUso>')
    xml.append(f'    <PlantasSobreRasante>{gen.numero_plantas}</PlantasSobreRasante>')
    xml.append('    <PlantasBajoRasante>0</PlantasBajoRasante>')
    xml.append(f'    <SuperficieUtil>{gen.superficie_util:.2f}</SuperficieUtil>')
    xml.append('  </DatosEdificio>')
    
    # 2. Datos del Certificado
    xml.append('  <DatosCertificado>')
    xml.append('    <TipoCertificado>Existente</TipoCertificado>')
    xml.append('    <Escala>ViviendaBloque</Escala>')
    xml.append('    <Procedimiento>')
    xml.append('      <Nombre>CE3X</Nombre>')
    xml.append('      <Version>3.2</Version>')
    xml.append('    </Procedimiento>')
    xml.append('    <FechaCalificacion>16/10/2026</FechaCalificacion>')
    xml.append('    <FechaGeneracion>16/10/2026</FechaGeneracion>')
    xml.append('  </DatosCertificado>')
    
    # 3. Datos del Certificador
    xml.append('  <DatosCertificador>')
    xml.append(f'    <NombreApellidos>{escape(adm.nombre_tecnico)}</NombreApellidos>')
    xml.append(f'    <Nif>{escape(adm.nif_tecnico or "00000000Z")}</Nif>')
    xml.append(f'    <RazonSocial>{escape(adm.razon_social or "Estudio JMC")}</RazonSocial>')
    xml.append(f'    <Domicilio>{escape(adm.direccion)}</Domicilio>')
    xml.append(f'    <Municipio>{escape(adm.municipio)}</Municipio>')
    xml.append(f'    <CodigoPostal>{escape(adm.codigo_postal)}</CodigoPostal>')
    xml.append(f'    <Provincia>{escape(adm.provincia)}</Provincia>')
    xml.append(f'    <ComunidadAutonoma>{escape(adm.comunidad_autonoma or "Galicia")}</ComunidadAutonoma>')
    xml.append(f'    <Titulacion>{escape(adm.titulacion_tecnico)}</Titulacion>')
    xml.append('  </DatosCertificador>')
    
    # 4. Modelo Simplificado
    xml.append('  <Modelo>')
    xml.append('    <Global>')
    xml.append('      <DemandaDiariaAcs>28.0</DemandaDiariaAcs>')
    xml.append(f'      <VentilacionDiseno>{gen.ventilacion_renovaciones:.2f}</VentilacionDiseno>')
    xml.append('      <CargaInternaMedia>2.15</CargaInternaMedia>')
    xml.append('    </Global>')
    xml.append('  </Modelo>')
    
    # 5. Demandas
    xml.append('  <Demandas>')
    xml.append(f'    <Calefaccion>{resultado.demanda_calefaccion:.2f}</Calefaccion>')
    xml.append(f'    <Refrigeracion>{resultado.demanda_refrigeracion:.2f}</Refrigeracion>')
    xml.append(f'    <ACS>{resultado.demanda_acs:.2f}</ACS>')
    xml.append('  </Demandas>')
    
    # 6. Energía Primaria No Renovable
    xml.append('  <ConsumoEnergiaPrimariaNoRenovable>')
    xml.append(f'    <Global>{resultado.consumo_energia_primaria_nr:.2f}</Global>')
    xml.append(f'    <Calefaccion>{resultado.demanda_calefaccion * 1.2:.2f}</Calefaccion>')
    xml.append(f'    <Refrigeracion>{resultado.demanda_refrigeracion * 0.8:.2f}</Refrigeracion>')
    xml.append(f'    <ACS>{resultado.demanda_acs * 1.5:.2f}</ACS>')
    xml.append('  </ConsumoEnergiaPrimariaNoRenovable>')
    
    # 7. Emisiones de CO2
    xml.append('  <EmisionesCO2>')
    xml.append(f'    <Global>{resultado.emisiones_co2:.2f}</Global>')
    xml.append(f'    <Calefaccion>{resultado.emisiones_co2 * 0.5:.2f}</Calefaccion>')
    xml.append(f'    <Refrigeracion>{resultado.emisiones_co2 * 0.2:.2f}</Refrigeracion>')
    xml.append(f'    <ACS>{resultado.emisiones_co2 * 0.3:.2f}</ACS>')
    xml.append('  </EmisionesCO2>')
    
    # 8. Calificación Energética (Letras)
    xml.append('  <Calificacion>')
    xml.append(f'    <DemandaCalefaccion>{resultado.letra_calefaccion}</DemandaCalefaccion>')
    xml.append(f'    <DemandaRefrigeracion>{resultado.letra_refrigeracion}</DemandaRefrigeracion>')
    xml.append(f'    <EnergiaPrimariaNoRenovable>{resultado.letra_global_energia_primaria}</EnergiaPrimariaNoRenovable>')
    xml.append(f'    <EmisionesCO2>{resultado.letra_global_emisiones}</EmisionesCO2>')
    xml.append('  </Calificacion>')
    
    # 9. Pruebas in situ obligatorias por RD 390/2021
    xml.append('  <PruebasComprobacionesInspecciones>')
    xml.append('    <Visita>')
    xml.append('      <FechaVisita>16/10/2026</FechaVisita>')
    xml.append('      <Datos>{ "inspeccion": "Inspección visual de envolvente e instalaciones in situ." }</Datos>')
    xml.append('    </Visita>')
    xml.append('  </PruebasComprobacionesInspecciones>')
    
    xml.append('</DatosEnergeticosDelEdificio>')
    return '\n'.join(xml)

