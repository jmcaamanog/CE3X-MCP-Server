# 📜 Registro de Versiones (Changelog) - CE3X-MCP-Server

En este documento se detalla la evolución y el lanzamiento oficial del servidor **CE3X-MCP-Server**, la plataforma oficial de interoperabilidad entre Modelos de Lenguaje (IA) y el motor oficial de certificación energética de edificios de España **CE3X v3.2**, conforme al **Real Decreto 390/2021** y al **Código Técnico de la Edificación (CTE DB-HE)**.

---

### Versión 1.5.1 — 17/10/2026: 🚀 Desacoplamiento de CI, Saneamiento de Superficies HVAC, Medidas de Mejora RD 390 y Seguridad DevSecOps

Actualización de estabilidad, rigor técnico y experiencia de usuario que consolida el flujo integral de certificación sin bloqueos en la interfaz gráfica de CE3X v3.2 y optimiza la infraestructura de CI/CD:

1. **Saneamiento Matemático de Instalaciones Térmicas en el Codec CEX**:
   * Corrección definitiva del modal de error de CE3X *"La instalación de calefacción cubre una demanda superior al 100%"*:
   * Se implementó un algoritmo de prorrateo y escalado proporcional de superficies útiles habitables para generadores térmicos coexistentes, garantizando que la suma de áreas asignadas nunca exceda la superficie útil total del inmueble (`superficie_util = 95.85 m²`).
   * Validación satisfactoria en vivo en la GUI oficial de CE3X v3.2: cálculo instantáneo de la etiqueta energética (**Letra E, 45.7 kgCO2/m²**).

2. **Inyección Reglamentaria de Medidas de Mejora (RD 390/2021) en XML Oficial 3.0**:
   * Estructuración automática de los 3 paquetes oficiales de rehabilitación reglamentarios (SATE, Aerotermia y Solución Integral con Solar Fotovoltaica) en el nodo `<MedidasMejora>` del XML oficial v3.0.
   * Homologación estricta con el esquema ministerial RelaxNG (`DatosEnergeticosDelEdificioSchema30-full.rng`), aplicando los enumerados normativos válidos para coste (`COSTE_MEDIDA`: `Medio`, `MuyAlto`) y plazo de recuperación (`PLAZO_RECUPERACION`: `Medio`, `Largo`).
   * Generación automática del dictamen técnico comparativo de ahorro y deducciones de IRPF y subvenciones Next Generation EU (RD 853/2021) en PDF maquetado profesionalmente con PyMuPDF.

3. **Desacoplamiento y Resiliencia en GitHub Actions (CI / Test Suite)**:
   * Empaquetado oficial del recurso `Escala/Localidades.xml` dentro del paquete (`src/ce3x_mcp/resources/Localidades.xml`), permitiendo que el servidor MCP ejecute cálculos de escalas y calificaciones oficiales en cualquier entorno (CI, contenedores Docker o servidores Linux) sin requerir tener instalado localmente el software de escritorio CE3X v3.2.
   * Detección contextual del entorno en la batería de pruebas: valida ejecutables locales (`xml2cert.exe`, `CE3Xv3.2.exe`) cuando están presentes y ejecuta las pruebas analíticas, catastrales y matemáticas de forma desacoplada en los runners en la nube de GitHub Actions (`windows-latest` en Azure).
   * Corrección de rutas estáticas en `sys.path` a resolución dinámica relativa al repositorio.

4. **Blindaje de Seguridad y DevSecOps en Repositorio GitHub**:
   * Desindexación de Git y exclusión en `.gitignore` de scripts de mantenimiento de PyPI (`subir_a_pypi.bat`), manteniéndolos en local para el autor sin exponerlos públicamente.
   * Configuración de GitHub Advanced Security: activación de *Private Vulnerability Reporting* y *Push Protection* para prevenir la filtración accidental de credenciales o secretos en commits.

5. **Plantilla Canónica de Toma de Datos In Situ en Madrid (Datos 100% Ficticios)**:
   * Publicación de la plantilla de campo completa y cubierta `ejemplos/PLANTILLA_TOMA_DATOS_EJEMPLO_MADRID.txt` y en `ejemplos/visita_vivienda_ejemplo/INFORMACION/apuntes_visita.txt`.
   * Incluye datos exhaustivos pero enteramente ficticios para la Comunidad de Madrid (Zona D3, 1974, 94.20 m²): técnico ficticio colegiado, termo eléctrico de 100L, caldera de condensación de 25 kW, split inverter Daikin de 3.5 kW, desglose de huecos con RPT y PVC bajo emisivo, sombra de edificio enfrente y protocolo formal del Anexo IV del RD 390/2021.

---

### Versión 1.5.0 — 16/10/2026: 🛡️ Reingeniería Integral de Rigor Normativo, Conexión Real con CE3X y Purga de Plantillas (26 Herramientas)

Actualización mayor centrada en la veracidad técnica, eliminación radical de datos de ejemplo y conexión directa con el motor oficial de CE3X v3.2 instalado en el sistema:

1. **Nueva Herramienta #26: `verificar_conexion_ce3x`**:
   * Auditoría y comprobación en vivo de la presencia e integridad de la instalación local de CE3X v3.2 (`C:\Program Files (x86)\CE3Xv3.2`).
   * Verificación del ejecutable `CE3Xv3.2.exe`, motor de exportación Typst (`xml2cert.exe`), validador RelaxNG (`xmlcheck.exe`), base de datos de escalas oficiales (`Escala/Localidades.xml`), bases de datos climáticas (`Calculos/BDClima`) y entorno Java auxiliar.
   * Chequeo previo preceptivo en `generar_certificado_completo` para impedir la generación de certificaciones si no se detecta el programa oficial.

2. **Conexión Directa con Escalas Oficiales y Edificios de Referencia de CE3X**:
   * Sustitución completa de fórmulas heurísticas por el cálculo directo contra `Escala/Localidades.xml` para las 32 zonas climáticas y tipologías (Unifamiliar y Bloque).
   * Límites de corte oficiales (A a G) para emisiones totales de CO2, consumo de energía primaria no renovable y demanda de calefacción.
   * Detección y aviso normativo si no se especifican instalaciones reales, evitando suposiciones no contrastadas.

3. **Purga Radical de Datos Residuales de Ejemplos en XML y PDF**:
   * Eliminación definitiva de todos los datos fantasma del Centro Juvenil de Madrid (7 viviendas, torre de refrigeración de 1006 kW, UTAs, fechas desfasadas y empresa de prueba).
   * Generación limpia de generadores térmicos con identificadores UUID v4 válidos y normalización estricta de provincias y comunidades autónomas según RelaxNG.
   * Normalización automática de titulaciones habilitantes (ej. *Arquitectura técnica o aparejadores*) conforme a los tipos del esquema ministerial.
   * El PDF oficial compilado con `xml2cert.exe` refleja única y exclusivamente los datos del inmueble evaluado.

4. **Generador CEX Adaptativo sin Clones de CENER/Pamplona**:
   * Mutación binaria limpia en codificación Latin-1/CP1252 que sustituye dirección, referencia catastral (20 caracteres), año, superficie, zona climática y datos del técnico sin arrastrar la geometría ni el certificador de Pamplona.
   * Carga instantánea y fluida garantizada en la interfaz de CE3X v3.2.

5. **Saneamiento del Módulo de Catastro**:
   * Parser agnóstico de espacios de nombres XML para extraer con precisión la dirección oficial (`<ldt>`), el año real de construcción (`<ant>`), la superficie construida (`<sfc>`) y los elementos constructivos (`<lcons>`).

6. **Importación Perezosa (Lazy Import) de BIM**:
   * Eliminada la importación obligatoria en cabecera de `ifcopenshell` en `bim_parser.py`, permitiendo la instalación y arranque limpios con `pip install ce3x-mcp-server` sin requerir dependencias C++ opcionales.

---

### Versión 1.0.0 — 16/10/2026: 🚀 Lanzamiento Oficial (General Availability - GA)

Primera versión pública estable y consolidada del servidor MCP oficial, que implementa el mapeo exhaustivo del software ministerial CE3X v3.2, sus manuales técnicos y la normativa técnica española en **25 herramientas FastMCP oficiales**:

#### 🏛️ 1. Núcleo Normativo y Motor Oficial de Certificación
* **Compatibilidad Binaria Perfecta de Proyectos `.cex`:** Lector y escritor nativo en Python 3 de archivos de proyecto `.cex` de CE3X v3.2, utilizando deserialización segura `SafeUnpickler` (protocolo 0) y mutación quirúrgica con codificación Latin-1/CP1252 para prevenir excepciones en wxPython.
* **Generador y Validador de XML Oficial v3.0:** Generación de archivos XML reglamentarios según la especificación *DatosEnergeticosDelEdificio v3.0*, validados al 100% contra el esquema RelaxNG oficial del Ministerio de Vivienda y Agenda Urbana (`xmlcheck.exe`).
* **Compilación de PDF Homologado de 15 Páginas:** Integración con Typst y el compilador oficial `xml2cert.exe` (IETcc-CSIC) para la generación instantánea del certificado de eficiencia energética oficial completo con gráficos y anexos.
* **Ingesta Telemática del Catastro (OVC):** Conexión directa en tiempo real con la Sede Electrónica de Catastro para recuperar automáticamente año de construcción, superficie construida y localización mediante la Referencia Catastral (`consultar_catastro`).
* **Zonificación Climática Oficial CTE DB-HE:** Asignación automática de zonas climáticas (α1 a E1) según municipio, capital de provincia y corrección de altitud del CTE DB-HE Apéndice B (`determinar_zona_climatica`).

#### 📐 2. Envolvente Térmica, Sombras y Cálculos Normativos Avanzados
* **Inferencia de Envolvente Histórica:** Biblioteca de arquetipos constructivos de fachadas, cubiertas y huecos según el año de construcción (Pre-1979, NBE-CT-79, CTE 2006, CTE 2013 y CTE 2019 nZEB) con asignación de transmitancias $U$ por defecto (`estimar_envolvente_por_defecto`).
* **Cálculo de Transmitancia de Ventanas UNE-EN ISO 10077-1:** Cálculo por componentes de la transmitancia total del hueco $U_w$ ($U_g$ vidrio, $U_f$ marco, $\Psi_g$ intercalario y fracción de hueco) con comprobación de límites CTE (`calcular_transmitancia_ventana_iso10077`).
* **Puentes Térmicos Lineales DA DB-HE / 3:** Estimación reglamentaria de valores $\Psi$ (W/m·K) para frentes de forjado, contorno de huecos y pilares integrados en fachada (`calcular_puentes_termicos`).
* **Patrones de Sombra Estacionales:** Cálculo del factor reductor solar $F_{sh}$ para huecos con voladizos, retranqueos de mocheta y toldos (`calcular_sombras_hueco`), así como sombras por obstáculos remotos y edificios colindantes mediante ángulo de elevación $lpha = rctan(H/D)$ (`calcular_sombras_obstaculo_edificio_enfrente`).
* **Cálculo de Pequeño Terciario y Locales:** Determinación de potencia de iluminación ($W/m^2$), VEEI objetivo (CTE DB-HE 3) y caudales de ventilación exterior según RITE (`calcular_parametros_terciario_local_comercial`).

#### ⚙️ 3. Instalaciones Térmicas, ACS y Simulación Solar Satelital
* **Demanda de ACS Oficial CTE DB-HE 4:** Cálculo de la demanda obligatoria de agua caliente sanitaria a 60 °C ($l/día$ y $kWh/año$) según dotaciones por número de dormitorios y tabla mensual de temperatura de agua de red provincial (`calcular_demanda_acs_cte_he4`).
* **Parser Inteligente de Equipos Térmicos:** Reconocimiento de equipos a partir de fichas técnicas o fotos de placas (calderas estándar, condensación, gasóleo, efecto Joule, bombas de calor inverter, aerotermia, biomasa y VRF), con conversión de Watts a kW y cálculo de rendimiento estacional (`analizar_ficha_equipo_clima`).
* **Producción Fotovoltaica Satelital con PVGIS:** Conexión en vivo con la API oficial PVGIS de la Comisión Europea (JRC) con radiación satelital SARAH-2 para estimación de producción fotovoltaica real en autoconsumo (`calcular_produccion_fotovoltaica_pvgis`).

#### 🧪 4. Ensayos Oficiales y Auditoría de Campo (RD 390/2021)
* **Registro de Visita Presencial In Situ:** Justificación del cumplimiento estricto del Art. 8 del RD 390/2021 para el Anexo IV obligatorio (`registrar_visita_presencial`).
* **Ensayo de Hermeticidad Blower Door (UNE-EN ISO 9972):** Registro y cálculo de la tasa de renovación de aire $n_{50}$ y permeabilidad $q_{50}$ con diagnóstico de hermeticidad (`registrar_ensayo_estanqueidad_blower_door`).
* **Ensayo de Flujometría Térmica In Situ (UNE-EN ISO 9869-1):** Determinación experimental de la transmitancia real $U$ de muros mediante sondas de flujo térmico y gradiente de temperatura para justificar el nivel conocido de envolvente (`registrar_ensayo_flujometria_termica_in_situ`).
* **Contraste de Facturación Real vs Modelo:** Verificación de calibración del modelo energético contra consumos reales de electricidad, gas y gasóleo (`contrastar_consumo_facturas_reales`).

#### 🌿 5. Medidas de Mejora y Dictámenes NextGen EU (RD 853/2021)
* **Paquetes Oficiales de Rehabilitación Energética:** Generación automática de 3 paquetes del RD 390/2021 (Envolvente SATE, Aerotermia y Solución Integral con Fotovoltaica) con cálculo de ahorro %, nuevo salto de letra (hasta letra A), inversión estimada y amortización (payback) (`proponer_medidas_mejora_rd390`).
* **Dictamen Justificativo de Ayudas Públicas e IRPF:** Acreditación del cumplimiento del umbral mínimo del 30% de reducción en energía primaria no renovable para la tramitación de subvenciones NextGen (RD 853/2021) en sus tramos del 40%, 65% y 80%, y deducciones del 40%/60% en IRPF (`emitir_dictamen_subvenciones_nextgen`).

#### 📁 6. Arquitectura Canónica de Visita y Ecosistema de Despliegue
* **Estructura Estándar de 5 Carpetas:** Organización profesional de los archivos del inmueble en `INFORMACION/`, `PLANOS/`, `FOTOS/`, `INSTALACIONES/` y `CERTIFICADO/`.
* **Auto-Organizador Inteligente:** Clasificación automática de archivos sueltos depositados en la raíz hacia sus subcarpetas correspondientes (`organizar_carpeta_visita`), auditoría asistida (`auditar_carpeta_visita`) y generación integral de entregables en la subcarpeta `CERTIFICADO/` (`certificar_desde_carpeta_visita`).
* **Firma y Perfil Técnico Colegial Persistente:** Almacenamiento seguro en `~/.ce3x_mcp_perfil_tecnico.json` para autorrellenado de credenciales del técnico en todos los documentos generados (`configurar_perfil_tecnico_colegiado`).
* **Instalador Automático de 1 Clic para Windows:** Script autoejecutable [`instalar_en_claude_desktop.bat`](./instalar_en_claude_desktop.bat) para inyección inmediata en Claude Desktop y Cursor.
* **Paquete Oficial en PyPI:** Disponible en el Python Package Index (`pip install ce3x-mcp-server`) y ejecutable instantáneamente sin instalación previa con `uvx --from ce3x-mcp-server ce3x-mcp`.
* **Ecosistema Multimodelo de Skills:** Manuales operativos y directivas de razonamiento adaptadas a los estándares de Google Gemini, Anthropic Claude y OpenAI GPT.
* **Batería de Pruebas y Validación (100% Passed):** Suite de 9 pruebas de integración y 7 matrices de escenarios (muros, HVAC, orientaciones, sombras, ventanas ISO 10077, ACS HE4 y ayudas públicas) totalmente verificada.
