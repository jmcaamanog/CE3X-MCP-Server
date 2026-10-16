# 🚀 Release v1.0.0 — CE3X-MCP-Server: Servidor MCP Oficial para Certificación Energética

> **Autor:** Jose Manuel Caamaño González | Arquitecto Técnico & BIM Manager  
> **Licencia:** MIT | **Normativa:** RD 390/2021 & CTE DB-HE | **Software:** CE3X v3.2 Oficial  
> **Tag Oficial Git:** `v1.0.0` / `v1.3.0`  
> **Paquetes Generados:** `dist/ce3x_mcp_server-1.3.0-py3-none-any.whl` | `dist/ce3x_mcp_server-1.3.0.tar.gz`

---

## 🌟 Hito Mayor: El Primer Ecosistema de Certificación Energética Oficial Asistido por IA

Este lanzamiento marca la publicación del **primer servidor oficial MCP (Model Context Protocol)** que conecta cualquier Inteligencia Artificial (**Claude, Cursor, Gemini**) con el motor oficial de certificación energética de España **CE3X v3.2** (reconocido por el Ministerio para la Transición Ecológica y el Reto Demográfico y el IDAE).

---

## 📦 Paquetes y Distribuciones Oficiales Disponibles

| Paquete / Archivo | Tamaño | Propósito / Instalación |
| :--- | :---: | :--- |
| **`ce3x_mcp_server-1.3.0-py3-none-any.whl`** | ~55 KB | Rueda de instalación Python universal (Wheel). `pip install ce3x_mcp_server-1.3.0-py3-none-any.whl` |
| **`ce3x_mcp_server-1.3.0.tar.gz`** | ~57 KB | Código fuente empaquetado para distribución (sdist). |
| **`instalar_en_claude_desktop.bat`** | ~1 KB | Instalador ejecutable en 1 clic para Windows (Claude Desktop y Cursor). |
| **`uvx ce3x-mcp`** | Nube | Ejecución inmediata en la nube sin clonar ni descargar código local. |

---

## 🛠️ Capacidades Destacadas del Ecosistema v1.0

### 1. Ingesta Multimodal y Catastro Telemático
- Conexión en vivo con la **Sede Electrónica de Catastro (OVC)** para extraer año, superficie y dirección con solo la Referencia Catastral.
- Lectura de planos arquitectónicos en **PDF** y modelos digitales **BIM IFC** (IfcOpenShell).
- Detección automática de calderas, aerotermias y bombas de calor por fotos de placas de características.

### 2. Compatibilidad Binaria Absoluta con CE3X v3.2 (.CEX)
- Ingeniería inversa del formato nativo CE3X (Python 2.7 congelado + serialización `pickle` protocolo 0 con deduplicación por memoización).
- Codificación obligatoria en **Latin-1 / CP1252** para tildes y eñes (`\xf1` para `ñ`), evitando cierres de Cython.
- Proyectos 100% verificados y listos para abrir y recalcular en la interfaz gráfica oficial.

### 3. Salida Oficial de Registro en `CERTIFICADO/`
- **`Certificado_Oficial_Registro.xml`:** XML oficial versión 3.0 validado contra el esquema RelaxNG del Ministerio.
- **`Informe_Certificacion_Energetica.pdf`:** Certificado legal completo de 15 páginas compilado con Typst / `xml2cert.exe`.
- **`Informe_Medidas_Mejora_NextGen.pdf/.md`:** Dictamen técnico oficial con cálculo de ahorro %, salto de letra y tramos de subvención del 40%, 65% y 80% (RD 853/2021) y deducciones IRPF.

### 4. Arquitectura de 5 Carpetas y Auto-Organizador Inteligente
- Estructuración automática de la visita en: `INFORMACION/`, `PLANOS/`, `FOTOS/`, `INSTALACIONES/` y `CERTIFICADO/`.
- Auto-clasificación de archivos sueltos mediante la herramienta `organizar_carpeta_visita`.

### 5. Catálogo de 22 Herramientas Oficiales
- Incluye cálculo de sombras de huecos ($F_{sh}$), sombras lejanas por edificios colindantes, puentes térmicos lineales (DA DB-HE / 3), ensayo de estanqueidad Blower Door (UNE-EN ISO 9972), contraste de facturas reales de luz/gas, radiación satelital PVGIS y parámetros de terciario/locales comerciales.

---

## 🧠 Skill Oficial para IA Incluida
El lanzamiento incluye la Skill [`skills/ce3x-certificacion-energetica/SKILL.md`](../skills/ce3x-certificacion-energetica/SKILL.md), compatible con **Claude Desktop/Projects**, **Custom GPTs de OpenAI** y **Google Gemini**, proporcionando a la IA la mentalidad y el protocolo técnico de un Arquitecto Técnico colegiado.
