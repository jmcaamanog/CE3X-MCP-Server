# 📋 Plantilla Inteligente de Toma de Datos para Certificación Energética (CE3X + IA)

Esta plantilla está especialmente optimizada para que un técnico o propietario rellene los datos (o los dicte por voz) y se los pegue directamente a su Asistente de IA (Claude, Gemini, Cursor, ChatGPT). La IA procesará la información automáticamente y ejecutará las herramientas del servidor **CE3X-MCP-Server**.

---

## 🏛️ 1. Datos Administrativos y Localización
* **Referencia Catastral (20 caracteres):** `[Ej: 000200100VK38C0001WX]` *(Si se facilita, la IA extraerá automáticamente dirección, año y superficie oficial)*
* **Dirección Completa:** `[Calle / Avenida, Número, Piso, Letra]`
* **Municipio y Provincia:** `[Ej: A Coruña, Madrid, Sevilla...]`
* **Código Postal:** `[Ej: 15003]`
* **Año de Construcción:** `[Ej: 1985]` *(Si no se sabe, la IA lo obtendrá de Catastro)*
* **Superficie Útil de la Vivienda (m²):** `[Ej: 85.5 m²]`
* **Altura libre media de techos (m):** `[Por defecto 2.50 m]`

---

## 🧱 2. Envolvente Térmica (Muros, Ventanas y Cubiertas)

### A. Fachadas Exteriores
* **Orientación principal:** `[Norte, Sur, Este, Oeste]`
* **Tipología de muro (si se conoce):**
  - [ ] **Desconocido:** *(La IA asignará la transmitancia U oficial según el año del edificio y la norma histórica NBE-CT-79 o CTE)*.
  - [ ] **Muro de piedra / ladrillo macizo antiguo (sin aislamiento):** U ≈ 1.80 - 2.20 W/m²K.
  - [ ] **Doble hoja con cámara de aire estándar (1980 - 2006):** U ≈ 1.40 - 1.60 W/m²K.
  - [ ] **Fachada con aislamiento térmico (SATE o cámara con lana mineral/EPS):** U ≈ 0.35 - 0.50 W/m²K.

### B. Ventanas y Huecos
* **Tipo de marco:**
  - [ ] **Aluminio simple sin rotura de puente térmico (RPT):** U ≈ 5.7 W/m²K.
  - [ ] **Aluminio con RPT (rotura de puente térmico):** U ≈ 2.8 - 3.2 W/m²K.
  - [ ] **PVC o Madera estándar:** U ≈ 2.0 - 2.2 W/m²K.
  - [ ] **PVC de alta eficiencia con triple vidrio:** U ≈ 1.0 - 1.3 W/m²K.
* **Tipo de vidrio:**
  - [ ] **Vidrio simple (monolítico 4 mm):** U ≈ 5.7 W/m²K.
  - [ ] **Doble vidrio con cámara de aire (tipo Climalit 4/6/4 o 4/12/4):** U ≈ 2.8 - 3.1 W/m²K, g = 0.75.
  - [ ] **Doble vidrio bajo emisivo:** U ≈ 1.4 - 1.8 W/m²K, g = 0.60.
* **Protecciones solares:** `[Persiana enrollable PVC/aluminio, toldo, voladizo]`

---

## ♨️ 3. Instalaciones Térmicas (Calefacción, ACS y Refrigeración)

### A. Agua Caliente Sanitaria (ACS)
* **Sistema:**
  - [ ] **Termo eléctrico:** Capacidad `[Ej: 80 L]`, Potencia `[Ej: 1.5 kW]`.
  - [ ] **Caldera mixta de Gas Natural:** Potencia `[Ej: 24 kW]`, Modelo `[Ej: Saunier Duval Thema Condens]`.
  - [ ] **Caldera de Gasóleo:**
  - [ ] **Bomba de calor / Aerotermia:** SCOP `[Ej: 3.2]`.

### B. Calefacción
* **Sistema:**
  - [ ] **Misma caldera que para ACS (caldera mixta con radiadores de agua)**.
  - [ ] **Radiadores eléctricos / Emisores térmicos (Efecto Joule)**.
  - [ ] **Bomba de calor split aire-aire:** Potencia `[Ej: 3.5 kW]`, SCOP `[Ej: 4.0]`.
  - [ ] **Calefacción central del edificio con contadores individuales / sin contadores**.

### C. Refrigeración (Aire Acondicionado)
* **¿Dispone de aire acondicionado?** `[Sí / No]`
* **Si dispone:** Split aire-aire, SEER `[Ej: 5.5]`.

---

## 📸 4. Fotos y Adjuntos Recomendados (Para análisis multimodal de la IA)
* [ ] **Foto de la placa de características de la caldera o termo** *(para leer modelo, kW y marcado CE)*.
* [ ] **Foto o escaneo del plano de distribución o croquis acotado**.
* [ ] **Foto de detalle de una ventana** *(para identificar RPT y cámara de vidrio)*.
* [ ] **Foto de la fachada exterior del edificio**.

---

## 💬 5. Ejemplo de Prompt Rápido para Pegar a tu IA:
> *"Hola, actúa como técnico certificador utilizando el servidor CE3X-MCP-Server. Tengo una vivienda en A Coruña construida en 1985 con referencia catastral 000200100VK38C0001WX. Tiene 95 m² útiles, ventanas de aluminio con climalit cambiadas en 2010 y una caldera Saunier Duval de gas natural de 24 kW para calefacción y ACS. Por favor, consulta el catastro, calcula la calificación energética estimada, propón las 3 medidas de mejora oficiales de rehabilitación y genera el proyecto .cex, el XML oficial y el PDF de 15 páginas."*
