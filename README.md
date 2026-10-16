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
| **Documento de Análisis** | 📄 **[Ver Análisis CE3X & MCP](./docs/analisis_ce3x_mcp_framework.md)** | Análisis exhaustivo del software, manuales técnicos y arquitectura. |
| **Historial de Versiones** | 📜 **[Ver Changelog](./CHANGELOG.md)** | Registro detallado de versiones y mejoras implementadas. |
| **Repositorio GitHub** | 💻 **[GitHub jmcaamanog](https://github.com/jmcaamanog/CE3X-MCP-Server)** | Código fuente, issues y lanzamientos oficiales. |

---

> [!IMPORTANT]
> ### 📥 Instalación Rápida para Clientes MCP (Claude Desktop, Cursor, Antigravity)
> Para integrar este servidor en tu cliente de IA favorito:
> `ash
> # Ejecución directa con uvx (sin instalación manual):
> uvx --from git+https://github.com/jmcaamanog/CE3X-MCP-Server ce3x-mcp
> `
> O mediante instalación local con pip:
> `ash
> git clone https://github.com/jmcaamanog/CE3X-MCP-Server.git
> cd CE3X-MCP-Server
> pip install -e .
> `

---

## 🌟 Características Principales (ConTech & AI Cert)

| Módulo | Icono | Funcionalidades Destacadas |
| :--- | :---: | :--- |
| **Ingesta Catastral Automática** | 🏛️ | Conexión directa con la **Sede Electrónica del Catastro (OVC)** para extraer datos oficiales, año de edificación, superficie y dirección con solo la Referencia Catastral. |
| **Motor Normativo CTE DB-HE** | 📐 | Determinación automática de **zonas climáticas CTE (α1 a E1)** con corrección por altitud y asignación de transmitancias límite e históricas (NBE-CT-79, CTE 2006/2013/2019). |
| **Exportación a CE3X (.cex)** | 💾 | Generación y lectura nativa de archivos de proyecto **.cex** para abrir, auditar y recalcular en la interfaz oficial de CE3X v3.2. |
| **XML Oficial de Registro** | 📑 | Creación de archivos XML normalizados conforme a la especificación **DatosEnergeticosDelEdificio v3.0**, validados contra el esquema RelaxNG oficial del Ministerio. |
| **Compilación de PDF Homologado** | 🖨️ | Integración con **Typst / xml2cert** (IETcc-CSIC) para compilar en segundos el certificado oficial completo de 8 a 15 páginas con gráficos y anejos. |
| **Medidas de Mejora Inteligentes** | 🌿 | Propuesta automatizada de paquetes de rehabilitación (SATE, aerotermia, fotovoltaica) con cálculo de ahorro %, nuevo salto de letra y periodo de retorno económico. |

---

## 🚀 Configuración en Clientes MCP

### Configuración en claude_desktop_config.json
`json
{
  \"mcpServers\": {
    \"ce3x\": {
      \"command\": \"python\",
      \"args\": [
        \"-m\",
        \"ce3x_mcp.server\"
      ]
    }
  }
}
`

---

## 👨‍💻 Autor y Dirección Técnica

**Jose Manuel Caamaño González** | Arquitecto Técnico & BIM Manager  
Digital Product Lead | ConTech & Digital Twin SaaS | Data Analytics (SQL, Power BI)  

Hecho con código y café desde A Coruña. ☕  
[LinkedIn](https://www.linkedin.com/in/jmcaamanog/) · [Web](https://jmcaamanog.pages.dev)
