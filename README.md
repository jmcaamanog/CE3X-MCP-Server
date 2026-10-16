# 🏢 CE3X-MCP-Server (Certificación Energética con IA & FastMCP)

| 🏗️ Perfil & ConTech | 📈 Repositorio & Enlaces |
| :--- | :--- |
| ![Profesión](https://img.shields.io/badge/Profesi%C3%B3n-Arquitectos%20T%C3%A9cnicos-2e7d32?logo=micro%3Abit&logoColor=white&style=plastic) <br> ![Role](https://img.shields.io/badge/Role-BIM%20%26%20ConTech-007ACC?logo=bim360&style=plastic) <br> ![Location](https://img.shields.io/badge/Location-A%20Coru%C3%B1a%20%F0%9F%8C%8A-005B94?logo=lighthouse&logoColor=white&style=plastic) <br> ![Sector](https://img.shields.io/badge/Sector-ConTech%20%7C%20AECO-E65100?logo=construct3&style=plastic) <br> ![Protocol](https://img.shields.io/badge/Protocol-Model%20Context%20Protocol-8A2BE2?logo=anthropic&style=plastic) <br> ![Engine](https://img.shields.io/badge/Engine-FastMCP%20%26%20Typst-10b981?logo=python&style=plastic) <br> ![Normativa](https://img.shields.io/badge/Normativa-CTE%20DB--HE%20%7C%20RD%20390%2F2021-d97706?style=plastic) <br> ![Language](https://img.shields.io/badge/Language-Python%203.11-3776AB?logo=python&logoColor=white&style=plastic) | [![Versión](https://img.shields.io/github/v/release/jmcaamanog/CE3X-MCP-Server?label=Version&color=3b82f6&logo=github&style=plastic)](https://github.com/jmcaamanog/CE3X-MCP-Server/releases/latest) <br> [![Stars](https://img.shields.io/github/stars/jmcaamanog/CE3X-MCP-Server?style=plastic&label=Stars&color=f59e0b&logo=github)](https://github.com/jmcaamanog/CE3X-MCP-Server/stargazers) <br> [![Licencia](https://img.shields.io/badge/Licencia-MIT-8b5cf6.svg?style=plastic)](./LICENSE) <br> [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=plastic&logo=linkedin)](https://www.linkedin.com/in/jmcaamanog/) <br> [![Web](https://img.shields.io/badge/Web-jmcaamanog.pages.dev-005B94?style=plastic)](https://jmcaamanog.pages.dev) |

### Servidor MCP Oficial para Automatizar Certificados de Eficiencia Energética con IA (Claude, Gemini, Cursor)
*Diseñado bajo la perspectiva técnica de un Arquitecto Técnico & BIM Manager para dotar al sector AECO de una herramienta libre, rigurosa y ultrarrápida.*

---

## ⚡ Enlaces y Accesos Rápidos

| 🌟 Recurso | 🚀 Acción / Enlace | 📝 Descripción |
| :--- | :--- | :--- |
| **Estudio de Conectores** | 🌐 **[Ver Estudio Integral de Conexiones](./docs/ESTUDIO_INTEGRAL_CONECTORES_CE3X_MCP.md)** | Mapeo pantalla a pantalla y botón a botón de CE3X a conectores de IA. |
| **Documento de Análisis** | 📄 **[Ver Análisis CE3X & MCP](./docs/analisis_ce3x_mcp_framework.md)** | Análisis exhaustivo del software, manuales técnicos y arquitectura modular. |
| **Entregables de Ejemplo** | 📁 **[Ver Carpeta de Ejemplos Generados](./ejemplos/)** | Archivos .cex, XML oficial v3.0 y PDF de 15 páginas generados en vivo. |
| **Historial de Versiones** | 📜 **[Ver Changelog](./CHANGELOG.md)** | Registro detallado de versiones y mejoras implementadas. |
| **Repositorio GitHub** | 💻 **[GitHub jmcaamanog](https://github.com/jmcaamanog/CE3X-MCP-Server)** | Código fuente, issues y lanzamientos oficiales. |

---

## 👥 Perfiles y Modos de Uso para Cualquier Profesional

| Perfil / Modo | Icono | Descripción del Flujo | Entrada Requerida | Entregables Generados |
| :--- | :---: | :--- | :--- | :--- |
| **Modo Express (Datos Mínimos)** | ⚡ | **Certificación ultrarrápida en segundos** interactuando por chat. La IA infiere automáticamente la envolvente y el clima normativo oficial. | Referencia Catastral (o municipio) + año + superficie + climatización básica. | Archivo `.cex`, XML oficial v3.0 homologado y **PDF oficial de 15 páginas**. |
| **Modo Técnico Documental** | 📐 | **Extracción multimodal asistida por IA**. Lee planos arquitectónicos en PDF y fotos de placas de características de equipos térmicos. | Plano de distribución en PDF/imagen + fotos o fichas técnicas de caldera/aerotermia. | Desglose completo de estancias, fachadas, ventanas, potencias y rendimientos estacionales (SCOP/COP). |
| **Modo BIM & Auditoría NextGen** | 🏗️ | **Conexión directa con modelos BIM** y justificación automática de subvenciones públicas y deducciones IRPF. | Archivo BIM `.ifc` (Revit, Archicad, CYPE) o proyecto de rehabilitación. | Cubicación BIM con `IfcOpenShell`, cálculo solar satelital PVGIS, salto a letra A y **Dictamen NextGen (RD 853/2021)**. |

---

> [!IMPORTANT]
> **🚀 Integración Instantánea en 1 Clic:** No necesitas compilar ni clonar nada si usas `uvx`. Copia y pega el bloque JSON correspondiente en tu cliente de IA (Claude Desktop, Cursor, Antigravity IDE o VS Code) y dispondrás de 11 herramientas oficiales en tu chat al instante.

---

## 🔌 Configuración Inmediata en Clientes de IA

### 1. Claude Desktop (`claude_desktop_config.json`)
Abre tu configuración de Claude Desktop (%APPDATA%\Claude\claude_desktop_config.json en Windows o ~/Library/Application Support/Claude/claude_desktop_config.json en macOS) y añade:

```json
{
  "mcpServers": {
    "ce3x": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/jmcaamanog/CE3X-MCP-Server.git",
        "ce3x-mcp"
      ]
    }
  }
}
```

### 2. Cursor IDE (`.cursor/mcp.json` o Settings > MCP)
En Cursor, ve a **Features > MCP Servers** o añade en tu archivo `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "ce3x": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/jmcaamanog/CE3X-MCP-Server.git",
        "ce3x-mcp"
      ]
    }
  }
}
```

### 3. Antigravity IDE / Gemini (`~/.gemini/config/mcp_config.json`)
```json
{
  "mcpServers": {
    "ce3x": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/jmcaamanog/CE3X-MCP-Server.git",
        "ce3x-mcp"
      ]
    }
  }
}
```

### 4. Instalación Local para Desarrollo (Opcional con `pip`)
Si prefieres tener el repositorio clonado y trabajar en local:

```bash
git clone https://github.com/jmcaamanog/CE3X-MCP-Server.git
cd CE3X-MCP-Server
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

Y en tu archivo de configuración MCP indicas el intérprete local:

```json
{
  "mcpServers": {
    "ce3x": {
      "command": "C:\\ruta\\al\\repositorio\\.venv\\Scripts\\python.exe",
      "args": [
        "-I",
        "-m",
        "ce3x_mcp.server"
      ],
      "env": {
        "PYTHONPATH": "C:\\ruta\\al\\repositorio\\src"
      }
    }
  }
}
```

---

## 🌟 Características Principales (ConTech & AI Cert)

| Módulo | Icono | Funcionalidades Destacadas |
| :--- | :---: | :--- |
| **Ingesta Catastral Automática** | 🏛️ | Conexión directa con la **Sede Electrónica del Catastro (OVC)** para extraer datos oficiales, año de edificación, superficie y dirección con solo la Referencia Catastral. |
| **Motor Normativo CTE DB-HE** | 📐 | Determinación automática de **zonas climáticas CTE (α1 a E1)** con corrección por altitud y asignación de transmitancias límite e históricas (NBE-CT-79, CTE 2006/2013/2019). |
| **Exportación a CE3X (.cex)** | 💾 | Generación y lectura nativa de archivos de proyecto **.cex** para abrir, auditar y recalcular en la interfaz oficial de CE3X v3.2. |
| **XML Oficial de Registro** | 📑 | Creación de archivos XML normalizados conforme a la especificación **DatosEnergeticosDelEdificio v3.0**, validados al 100% contra el esquema RelaxNG oficial del Ministerio. |
| **Compilación de PDF Homologado** | 🖨️ | Integración con **Typst / xml2cert** (IETcc-CSIC) para compilar en segundos el certificado oficial completo de 15 páginas con gráficos y anejos. |
| **Cálculo Solar Satelital PVGIS** | ☀️ | Conexión en vivo con la **API oficial PVGIS de la Comisión Europea** (JRC) para estimar la producción fotovoltaica real (kWh/año) según radiación satelital SARAH-2. |
| **Medidas de Mejora & NextGen** | 🌿 | Propuesta automatizada de paquetes de rehabilitación (SATE, aerotermia, fotovoltaica) con cálculo de ahorro %, nuevo salto de letra, amortización y **dictamen para ayudas RD 853/2021 y deducciones IRPF**. |

---

## 🛠️ Catálogo de Herramientas MCP Disponibles

Una vez conectado, cualquier usuario puede solicitar a su modelo de lenguaje acciones como:

1. `consultar_catastro(referencia_catastral)`: Ingesta de datos de catastro en un solo clic.
2. `determinar_zona_climatica(provincia, municipio, altitud)`: Clima reglamentario CTE DB-HE.
3. `estimar_envolvente_por_defecto(ano_construccion, zona_climatica, superficie_util)`: Transmitancias térmicas oficiales según la antigüedad del inmueble.
4. `calcular_calificacion_energetica(proyecto)`: Demandas, consumos, emisiones y letra global (A a G).
5. `analizar_modelo_bim_ifc(ifc_path)`: Extracción geométrica de envolvente térmica desde modelos BIM.
6. `analizar_plano_arquitectura_pdf(pdf_path)`: Reconocimiento inteligente de recintos, superficies y carpinterías.
7. `analizar_ficha_equipo_clima(texto_o_ficha)`: Lectura de potencias y rendimientos estacionales (SCOP/COP).
8. `calcular_produccion_fotovoltaica_pvgis(latitud, longitud, potencia_kwp)`: Simulación solar satelital real.
9. `proponer_medidas_mejora_rd390(...)`: Generación de los 3 paquetes oficiales de rehabilitación.
10. `emitir_dictamen_subvenciones_nextgen(...)`: Certificación de ahorros RD 853/2021 y deducción fiscal IRPF.
11. `generar_certificado_completo(...)`: Pipeline integral que emite el archivo `.cex`, el XML oficial v3.0 y el PDF de 15 páginas.

---

## 📁 Entregables de Prueba Incluidos en el Repositorio

En la carpeta [`ejemplos/`](./ejemplos/) encontrarás los entregables generados durante las pruebas oficiales de certificación:
* **[`Proyecto_Vivienda_Coruna_1985.cex`](./ejemplos/Proyecto_Vivienda_Coruna_1985.cex)**: Proyecto nativo editable en CE3X v3.2.
* **[`Certificado_Oficial_Coruna_1985.xml`](./ejemplos/Certificado_Oficial_Coruna_1985.xml)**: XML ministerial validado con `xmlcheck.exe`.
* **[`Certificado_Oficial_Coruna_1985.pdf`](./ejemplos/Certificado_Oficial_Coruna_1985.pdf)**: Certificado de Eficiencia Energética oficial de 15 páginas.

---

## 👨‍💻 Autor y Dirección Técnica

**Jose Manuel Caamaño González** | Arquitecto Técnico & BIM Manager  
Digital Product Lead | ConTech & Digital Twin SaaS | Data Analytics (SQL, Power BI)  

Hecho con código y café desde A Coruña. ☕  
[LinkedIn](https://www.linkedin.com/in/jmcaamanog/) · [Web](https://jmcaamanog.pages.dev)
