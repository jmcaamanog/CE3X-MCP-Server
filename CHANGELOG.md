# 📜 Registro de Versiones (Changelog) - CE3X-MCP-Server

En este documento se detalla la evolución completa del servidor oficial MCP para la integración de Inteligencia Artificial con el motor de certificación energética oficial de España **CE3X v3.2**, conforme al **RD 390/2021** y al **Código Técnico de la Edificación (CTE DB-HE)**.

---

### Versión 1.3.0 — 16/10/2026: 🚀 22 Herramientas Oficiales, Instalador 1-Clic e Integración PyPI

* **🖱️ Instalador Automático de 1 Clic para Windows (`instalar_en_claude_desktop.bat`):**
  - Script autoejecutable sin consola ni necesidad de conocimientos técnicos.
  - Localiza e inyecta de forma no destructiva la configuración de `ce3x` en Claude Desktop (`claude_desktop_config.json`) y Cursor IDE (`.cursor/mcp.json`).
* **📦 Preparación y Soporte Universal PyPI (`uvx ce3x-mcp`):**
  - Configuración dual de ejecutables de entrada en `pyproject.toml` (`ce3x-mcp` y `ce3x-mcp-server`).
* **🏢 Soporte Integral de Pequeño Terciario y Locales Comerciales (`calcular_parametros_terciario_local_comercial`):**
  - Cálculo de potencia de iluminación instalada ($W/m^2$), VEEI objetivo conforme a CTE DB-HE 3 y tasas de renovación de aire exterior según RITE (IDA 2 / IDA 3).
* **🏙️ Cálculo de Sombras por Obstáculo Remoto / Edificio Enfrente (`calcular_sombras_obstaculo_edificio_enfrente`):**
  - Cálculo angular de elevación $\alpha = \arctan(H/D)$ y factor reductor estacional $F_{sh}$ conforme a las tablas oficiales de obstáculos de CE3X y CTE DB-HE.
* **✍️ Perfil Técnico Colegial Persistente (`configurar_perfil_tecnico_colegiado`):**
  - Almacenamiento seguro en `~/.ce3x_mcp_perfil_tecnico.json` para autorrellenado automático de credenciales profesionales en `.cex`, XML y PDFs oficiales.
* **🧪 Batería de Pruebas Unitarias al 100%:** 22 herramientas FastMCP verificadas con 8 suites de tests pasando satisfactoriamente.

---

### Versión 1.2.0 — 16/10/2026: 🚀 Arquitectura de 5 Carpetas, Auto-Organizador y Ecosistema de Visita

* **📁 Arquitectura Estándar de 5 Subcarpetas para Cada Inmueble:**
  Estructuración canónica y profesional del directorio de visita en:
  - `INFORMACION/`: Notas de visita, Referencia Catastral, apuntes, datos del cliente y extractos de Catastro.
  - `PLANOS/`: Planos arquitectónicos de distribución (PDF), croquis acotados y modelos BIM (IFC/DWG).
  - `FOTOS/`: Fotografías generales del inmueble (fachada exterior, carpinterías/ventanas, vistas y sombras).
  - `INSTALACIONES/`: Fotos de placas de características de calderas, termos, bombas de calor y fichas técnicas.
  - `CERTIFICADO/`: Carpeta oficial de salida exclusiva para los entregables finales.
* **🧹 Auto-Organizador Inteligente (`organizar_carpeta_visita`):** Herramienta que clasifica y mueve automáticamente archivos sueltos depositados en la raíz o en carpetas no estándar hacia sus 5 subcarpetas correspondientes, generando además la ficha guía `LEEME_ESTRUCTURA_VISITA.txt`.
* **🤖 Protocolo de Primer Contacto con la IA:** Configuración de directivas en FastMCP para que lo primero que pregunte el asistente sea la ubicación de la carpeta de visita en el equipo local del usuario.
* **🏷️ Detección Inteligente de Equipos por Nombre de Foto:** Ingesta automática de tecnología, potencia y combustible a partir de los nombres de fotos depositadas en `INSTALACIONES/` (ej. calderas de condensación, bombas de calor, termos).

---

### Versión 1.1.0 — 16/10/2026: 🎯 Subcarpeta `CERTIFICADO/` y Generación Total de Entregables Oficiales

* **📦 Subcarpeta Oficial Automatizada `CERTIFICADO/`:** Creación automática y directa dentro de la carpeta del inmueble de un directorio limpio y exclusivo con todos los entregables generados:
  - `Proyecto_CE3X.cex`: Archivo nativo editable para CE3X v3.2.
  - `Certificado_Oficial_Registro.xml`: XML oficial v3.0 validado contra el esquema RelaxNG del Ministerio.
  - `Informe_Certificacion_Energetica.pdf`: Certificado oficial de 15 páginas compilado con Typst / `xml2cert.exe`.
  - `Informe_Medidas_Mejora_NextGen.pdf`: Dictamen técnico de medidas de mejora del RD 390/2021 y subvenciones NextGen (RD 853/2021) maquetado en PDF (PyMuPDF).
  - `Informe_Medidas_Mejora_NextGen.md`: Dictamen técnico completo en formato Markdown editable.
  - `RESUMEN_ENTREGA.txt`: Ficha resumen ejecutivo con letra energética, emisiones de CO2 y ayudas públicas estimadas.
* **⚡ Auditoría y Certificación de Extremo a Extremo:** Herramienta `@mcp.tool() certificar_desde_carpeta_visita` operativa al 100%.

---

### Versión 1.0.0 — 16/10/2026: 🚀 Hito Mayor: Servidor FastMCP y Compatibilidad CEX 100% Verificada

* **🟢 Compatibilidad Binaria Perfecta de Proyectos .CEX:**
  - Descubrimiento e ingeniería inversa del formato nativo CE3X (Python 2.7 congelado + serialización `pickle` protocol 0 con memoization deduplicada).
  - Corrección de codificación estricta en Latin-1 / CP1252 (`\xf1` para la letra `ñ`) para evitar fallos de decodificación en Cython.
  - Verificación exitosa en vivo en la interfaz de CE3X v3.2 de 3 proyectos reales generados (`Proyecto_1_RuaReal.cex`, `Proyecto_2_PlazaLugo.cex`, `Proyecto_3_CantonGrande.cex`).
* **🏛️ Catálogo Oficial de Arquetipos Constructivos Españoles (`libraries.py`):**
  - Inferencia automática de transmitancias térmicas $U$ de fachadas, cubiertas y huecos según el año de construcción y normativa vigente (Anterior a 1979, NBE-CT-79, CTE 2006, CTE 2013, CTE 2019 nZEB).
  - Catálogos de vidrios (simple, doble estándar, doble bajo emisivo) y marcos (madera, metálico sin RPT, aluminio con RPT, PVC).
* **🌐 Conectividad Oficial con Catastro de España:** Consulta telemática de la Sede Electrónica de Catastro vía OVS a partir de la Referencia Catastral (20 caracteres en territorio común o 29 en foral).
* **☀️ Integración Satelital PVGIS de la Comisión Europea:** Estimación de producción fotovoltaica en tiempo real con datos de radiación satelital oficial.
* **💶 Motor de Medidas de Mejora RD 390/2021 y Subvenciones NextGen (RD 853/2021):**
  - Cálculo de ahorro en Energía Primaria no Renovable (EPnr) y emisiones de CO2.
  - Determinación de tramos de subvención del 40%, 65% u 80% (hasta 18.800 € por vivienda) y deducciones en el IRPF del 40% y 60%.
* **📐 Extracción de Planos PDF y Modelos BIM IFC:** Extracción de superficies de recintos y cálculo de envolvente con IfcOpenShell y PyMuPDF.

---

*Jose Manuel Caamaño González | Arquitecto Técnico & BIM Manager*  
*A Coruña, Galicia. Hecho con código y café. ☕*
