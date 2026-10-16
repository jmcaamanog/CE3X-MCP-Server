# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y el proyecto sigue el estándar de [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-16

### Novedades
- Inicialización del proyecto **CE3X-MCP-Server** con arquitectura modular FastMCP.
- Núcleo de cálculo CTE DB-HE con tablas de zonas climáticas y factores de paso a energía primaria y emisiones de CO2 del IDAE.
- Módulo de consulta telemática a la Sede Electrónica del Catastro (OVC) por referencia catastral.
- Generador de archivos XML oficiales según especificación DatosEnergeticosDelEdificio version 3.0 (RelaxNG).
- Conector de compilación de PDF oficial mediante xml2cert (IETcc-CSIC / Typst).
- Lector y escritor bidireccional de archivos de proyecto nativos .cex de CE3X.
- Herramientas MCP registradas: consultar_catastro, determinar_zona_climatica, estimar_envolvente_por_defecto, calcular_calificacion_energetica, generar_certificado_completo.
- Batería de pruebas unitarias en 	ests/test_ce3x_mcp.py.
