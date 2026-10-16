# 🧠 Guía Oficial de Integración de Skills en Claude, ChatGPT y Gemini

> [!IMPORTANT]
> Esta guía explica cómo activar el manual operativo de la Skill **`ce3x-certificacion-energetica`** en los tres principales modelos de Inteligencia Artificial del mercado (**Claude**, **ChatGPT** y **Gemini**), para que razonen con el criterio técnico y normativo de un **Arquitecto Técnico colegiado especialista en eficiencia energética**.

---

## ❓ ¿Por qué una Skill no es redundante con el Servidor MCP?

Existe una diferencia fundamental entre el **Servidor MCP** y la **Skill de IA**:

| Componente | Qué representa | Función concreta |
| :--- | :--- | :--- |
| **Servidor MCP (`server.py`)** | **Los brazos y las manos** | Es la API ejecutable que realiza las acciones físicas: conectarse al Catastro telemático, calcular la fórmula del factor de sombras, serializar el archivo binario `.cex` y compilar el PDF de 15 páginas. |
| **La Skill (`SKILL.md`)** | **El cerebro y el criterio técnico** | Es el manual metodológico que le enseña a la IA **cómo pensar**: qué datos pedir, cómo interpretar una foto borrosa de caldera, cómo deducir la envolvente según el año de construcción, cuándo limitar las preguntas al técnico a 1 sola duda crítica y cómo justificar subvenciones NextGen. |

**Conclusión:** El MCP le da a la IA las herramientas; la Skill le da la **inteligencia profesional** para usarlas con rigor normativo y sin equivocarse.

---

## 🟣 1. Cómo activar la Skill en Anthropic Claude (Claude Desktop & Claude.ai)

### En Claude Desktop (con MCP Conectado):
1. Asegúrate de tener instalado el servidor con `instalar_en_claude_desktop.bat`.
2. En Claude Desktop, ve a **Settings > General > Custom Instructions** (o las instrucciones de tu proyecto).
3. Pega el contenido íntegro del archivo [`skills/ce3x-certificacion-energetica/SKILL.md`](../skills/ce3x-certificacion-energetica/SKILL.md).
4. A partir de ese momento, cada vez que le hables de un inmueble o le pases una carpeta de fotos, Claude asumirá el protocolo oficial en 4 fases de CE3X.

### En Claude.ai (Proyectos):
1. Crea un nuevo Proyecto llamado **"Certificación Energética CE3X"**.
2. En la sección **Project Knowledge**, sube o pega el archivo `SKILL.md`.
3. En **Project Instructions**, añade:
   > *"Actúa siguiendo estrictamente las directivas técnicas del archivo SKILL.md adjunto para auditar inmuebles, estimar transmitancias históricas y preparar la información para CE3X v3.2."*

---

## 🟢 2. Cómo activar la Skill en OpenAI ChatGPT (Custom GPT)

Para crear un GPT especializado en tu cuenta de ChatGPT Plus o Team:

1. Ve a **Explore GPTs > Create**.
2. En la pestaña **Configure**:
   - **Name:** `Asistente Oficial CE3X & Eficiencia Energética`
   - **Description:** `Arquitecto Técnico especialista en certificación energética oficial con CE3X v3.2, CTE DB-HE y ayudas NextGen.`
3. En el cuadro **Instructions**:
   - Pega el contenido completo del archivo [`skills/ce3x-certificacion-energetica/SKILL.md`](../skills/ce3x-certificacion-energetica/SKILL.md).
4. En **Knowledge**:
   - Puedes subir el archivo [`docs/PLANTILLA_TOMA_DATOS_CEE.md`](./PLANTILLA_TOMA_DATOS_CEE.md) y [`docs/ESTUDIO_INTEGRAL_CONECTORES_CE3X_MCP.md`](./ESTUDIO_INTEGRAL_CONECTORES_CE3X_MCP.md).
5. **Capacidades:** Habilita *Code Interpreter* y *Web Browsing* (para consultar referencias catastrales si fuera necesario).

---

## 🔵 3. Cómo activar la Skill en Google Gemini & Antigravity IDE

En el entorno de Antigravity IDE y Gemini, la Skill está **nativa y automáticamente integrada**:

1. El archivo se encuentra registrado en el directorio global:
   `C:\Users\Jose\.gemini\config\skills\ce3x-certificacion-energetica\SKILL.md`
2. En cualquier conversación con Gemini, el motor detecta la habilidad por su descripción YAML (`ce3x-certificacion-energetica`).
3. Puedes invocarla directamente en tu mensaje diciendo:
   > *"Usa la skill de ce3x-certificacion-energetica para auditar esta visita..."*
