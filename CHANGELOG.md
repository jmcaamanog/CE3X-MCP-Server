# 📜 Registro de Versiones (Changelog) - CE3X-MCP-Server

En este documento se detalla la evolución y el lanzamiento oficial del servidor **CE3X-MCP-Server**, la plataforma oficial de interoperabilidad entre Modelos de Lenguaje (IA) y el motor oficial de certificación energética de edificios de España **CE3X v3.2**, conforme al **Real Decreto 390/2021** y al **Código Técnico de la Edificación (CTE DB-HE)**.

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
