# 🧠 Directorio Oficial de Skills para IA (Gemini, Claude, OpenAI)

Este directorio contiene las habilidades y directivas de comportamiento del ecosistema **CE3X-MCP-Server**, optimizadas específicamente para los protocolos de desarrollo de cada plataforma de Inteligencia Artificial:

---

## 📂 Estructura del Directorio

| Carpeta | Plataforma de IA | Protocolo / Formato Utilizado | Archivo Principal |
| :--- | :--- | :--- | :--- |
| **📁 `skills/gemini/`** | **Google Gemini & Antigravity IDE** | **Agent Skills Standard** (Metadata YAML frontmatter `name/description` + Markdown detallado). | [`SKILL.md`](./gemini/SKILL.md) |
| **📁 `skills/claude/`** | **Anthropic Claude** | **Anthropic Prompt Engineering** (Etiquetas semánticas XML `<role>`, `<context>`, `<rules>`, `<workflow>`). | [`CLAUDE_PROJECT_INSTRUCTIONS.md`](./claude/CLAUDE_PROJECT_INSTRUCTIONS.md) |
| **📁 `skills/openai/`** | **OpenAI ChatGPT** | **Custom GPT Builder Standard** (Instrucciones directas, imperativas y concisas bajo el límite de 8.000 caracteres). | [`GPT_BUILDER_INSTRUCTIONS.md`](./openai/GPT_BUILDER_INSTRUCTIONS.md) |
| **📁 `skills/ce3x-certificacion-energetica/`** | **Universal / Canónica** | Manual operativo completo y exhaustivo de 9 secciones para consulta técnica humana y de agentes. | [`SKILL.md`](./ce3x-certificacion-energetica/SKILL.md) |

---

## ❓ ¿Por qué están separadas por IA?

Aunque el **contenido normativo de fondo es idéntico** (RD 390/2021, CTE DB-HE, CE3X v3.2 y las 22 herramientas FastMCP), cada motor de IA tiene un protocolo de atención diferente:
1. **Claude (Anthropic):** Es el modelo que mejor responde al etiquetado semántico XML. Usar etiquetas `<workflow>` y `<rules>` reduce las alucinaciones a cero y garantiza que jamás olvide la regla de hacer un máximo de 1 o 2 preguntas al técnico.
2. **ChatGPT (OpenAI):** El constructor de Custom GPTs impone un límite de caracteres en la caja de *Instructions*. El archivo de `skills/openai/` condensa toda la lógica en viñetas de alta densidad semántica sin sobrepasar el límite.
3. **Gemini (Google):** Utiliza la especificación formal de **Agent Skills**, donde el motor indexa las skills automáticamente leyendo el encabezado YAML (`name` y `description`).

---

## 🚀 Guía de Instalación en 30 Segundos

Para consultar las instrucciones exactas paso a paso de cómo activar cada una en tu cuenta o cliente, consulta la **[Guía Oficial de Integración de Skills](../docs/GUIA_SKILL_CLAUDE_GPT_GEMINI.md)**.
