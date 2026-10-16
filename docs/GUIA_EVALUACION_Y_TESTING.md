# 🧪 Guía Oficial de Evaluación y Testing Técnico para Profesionales (CE3X-MCP-Server)

> [!IMPORTANT]
> Esta guía está diseñada para que cualquier **Arquitecto, Arquitecto Técnico o Ingeniero** pueda evaluar, testear y someter a estrés el servidor **CE3X-MCP-Server** en su propio equipo en menos de 5 minutos, verificando la compatibilidad absoluta con el software oficial **CE3X v3.2** y la normativa **RD 390/2021**.

---

## ⚡ 1. Conexión Rápida en Clientes de IA (1 Minuto)

### Opción A: Claude Desktop (`claude_desktop_config.json`)
Abre tu configuración de Claude Desktop y añade el servidor en el bloque `mcpServers`:

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

### Opción B: Cursor IDE (`.cursor/mcp.json` o Settings > MCP)
Añade un nuevo servidor MCP tipo `command`:
- **Nombre:** `ce3x`
- **Comando:** `uvx --from git+https://github.com/jmcaamanog/CE3X-MCP-Server.git ce3x-mcp`

---

## 🚀 2. Prueba "Plug & Play" con la Carpeta de Ejemplo Incluida

El repositorio incluye una carpeta de toma de datos real lista para usar en:
📁 **`ejemplos/visita_vivienda_ejemplo/`**

### Paso 1: Inicia conversación con tu IA
Escribe a Claude, Gemini o Cursor:
> *"Hola, quiero certificar el inmueble de la carpeta `ejemplos/visita_vivienda_ejemplo` usando el MCP de CE3X."*

### Paso 2: Observa la auto-organización en 5 carpetas
Verás cómo el servidor ejecuta `organizar_carpeta_visita` y estructura los archivos automáticamente:
- `📁 INFORMACION/` -> `apuntes_visita.txt` (con Referencia Catastral `2344201XK3724S0001LD`).
- `📁 PLANOS/` -> `plano_distribucion_vivienda.pdf` (plano acotado de 88.50 m² útiles).
- `📁 FOTOS/` -> `foto_fachada_principal_sur.jpg`.
- `📁 INSTALACIONES/` -> `placa_caldera_gas_condensacion_25kW.jpg` y `foto_termo_electrico_80L.jpg`.
- `📁 CERTIFICADO/` -> Reservada para la salida oficial.

### Paso 3: Entrevista técnica quirúrgica
La IA auditará los datos y te hará únicamente **1 o 2 preguntas breves** (por ejemplo, si existen sombras acusadas en el patio de luces o si se confirma la orientación Sur).

### Paso 4: Generación completa de entregables
Al responder, la IA ejecutará `certificar_desde_carpeta_visita` y creará dentro de `CERTIFICADO/`:
1. **`Proyecto_CE3X.cex`**
2. **`Certificado_Oficial_Registro.xml`**
3. **`Informe_Certificacion_Energetica.pdf`**
4. **`Informe_Medidas_Mejora_NextGen.pdf`**
5. **`Informe_Medidas_Mejora_NextGen.md`**
6. **`RESUMEN_ENTREGA.txt`**

---

## 🖥️ 3. Verificación en el Software Oficial CE3X v3.2

Para contrastar el resultado en la aplicación oficial del Ministerio:

1. Abre **CE3X v3.2** en tu ordenador Windows.
2. Ve al menú superior: **Archivo > Abrir**.
3. Navega hasta la carpeta `ejemplos/visita_vivienda_ejemplo/CERTIFICADO/` y selecciona **`Proyecto_CE3X.cex`**.
4. **Comprueba los paneles:**
   - **Datos Administrativos:** Nombre del edificio, dirección completa, municipio, Referencia Catastral oficial (20 caracteres) y datos del técnico colegiado.
   - **Datos Generales:** Superficie útil (88.5 m²), año (1982), zona climática (C1 para A Coruña).
   - **Envolvente Térmica:** Fachadas con transmitancia por defecto NBE-CT-79 (U=1.20 W/m²K) y ventanas de aluminio con RPT y doble vidrio.
   - **Instalaciones:** Caldera de condensación a gas natural y termo eléctrico.
5. Pulsa el botón **"Calcular calificación energética"**: Verás cómo el motor oficial de CE3X ejecuta el cálculo sin errores y confirma la calificación.

---

## 🛡️ 4. Verificación del Archivo XML v3.0

El archivo `Certificado_Oficial_Registro.xml` cumple estrictamente con el esquema oficial `DatosEnergeticosDelEdificio` versión 3.0:
- Contiene los bloques obligatorios: `<DatosEdificio>`, `<DatosGenerales>`, `<EnvolventeTermica>`, `<InstalacionesTermicas>`, `<ResultadoCalificacion>`, `<MedidasDeMejora>` y `<InspeccionesObservaciones>`.
- Es 100% válido para su carga en las sedes telemáticas de registro de cualquier Comunidad Autónoma (Xunta de Galicia, Comunidad de Madrid, Generalitat, etc.).

---

## 📊 5. Checklist de Pruebas Adicionales Disponibles

Puedes probar en tu chat de IA cualquiera de las 20 herramientas oficiales:

| Prueba / Ensayo | Comando de Prueba sugerido a la IA |
| :--- | :--- |
| **Configurar tu firma** | *"Configura mi perfil de técnico: Nombre 'Laura Gómez', NIF '12345678X', Arquitecta Técnica, Colegiada 3421 de COAT Madrid."* |
| **Ensayo Blower Door** | *"Registra un ensayo Blower Door UNE-EN ISO 9972 para un volumen de 240 m3 con caudal a 50 Pa de 450 m3/h."* |
| **Puentes Térmicos** | *"Calcula los puentes térmicos según el CTE para un piso de 1995 con 35m de frente de forjado y 25m de huecos."* |
| **Contraste de Facturas** | *"Compara un consumo teórico de 6500 kWh/año con mis facturas reales: 3200 kWh de luz y 4100 kWh de gas."* |
| **Cálculo de Sombras** | *"Calcula el factor de sombra de una ventana al Sur con 1.40m de alto, retranqueo de 15cm y voladizo de 60cm."* |
| **Producción Solar PVGIS** | *"Calcula la producción fotovoltaica en A Coruña (lat 43.36, lon -8.41) para una instalación de 3.5 kWp."* |

---

*Jose Manuel Caamaño González | Arquitecto Técnico & BIM Manager*  
*A Coruña, Galicia. Hecho con código y café. ☕*
