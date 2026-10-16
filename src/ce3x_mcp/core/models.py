from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class DatosAdministrativos(BaseModel):
    nombre_edificio: str = Field(..., description="Nombre identificativo del edificio o vivienda")
    direccion: str = Field(..., description="Dirección completa del inmueble")
    municipio: str = Field(..., description="Municipio")
    provincia: str = Field(..., description="Provincia")
    codigo_postal: str = Field(..., description="Código Postal")
    comunidad_autonoma: Optional[str] = Field("Galicia", description="Comunidad Autónoma")
    referencia_catastral: Optional[str] = Field(None, description="Referencia catastral (20 caracteres)")
    tipo_alcance: Literal["EdificioCompleto", "ViviendaIndividual", "ParteEdificio"] = "ViviendaIndividual"
    titulacion_tecnico: str = "Arquitecto Técnico"
    nombre_tecnico: str = "Jose Manuel Caamaño González"
    nif_tecnico: Optional[str] = "00000000Z"
    razon_social: Optional[str] = "Estudio Técnico JMC"

class DatosGenerales(BaseModel):
    tipologia: Literal["Unifamiliar", "Bloque", "ViviendaBloque", "PequenoTerciario", "GranTerciario"] = "ViviendaBloque"
    ano_construccion: int = Field(1985, description="Año de construcción del edificio")
    normativa_vigente: Literal["Anterior1979", "NBE_CT_79", "CTE_2006", "CTE_2013", "CTE_2019"] = "NBE_CT_79"
    zona_climatica: str = Field("C1", description="Zona climática CTE (ej. C1, D3, A3, etc.)")
    superficie_util: float = Field(..., description="Superficie útil acondicionada en m²")
    altura_libre: float = Field(2.6, description="Altura libre media entre forjados en metros")
    numero_plantas: int = Field(1, description="Número de plantas del inmueble o vivienda")
    inercia_termica: Literal["Baja", "Media", "Alta"] = "Media"
    ventilacion_renovaciones: float = Field(0.63, description="Renovaciones de aire por hora (ren/h)")

class CerramientoOpaco(BaseModel):
    nombre: str
    tipo: Literal["FachadaAire", "FachadaTerreno", "Medianera", "CubiertaAire", "CubiertaTerreno", "SueloAire", "SueloTerreno", "ParticionInterior"] = "FachadaAire"
    orientacion: Literal["N", "S", "E", "O", "NE", "NO", "SE", "SO", "H"] = "N"
    superficie: float = Field(..., description="Superficie en m²")
    transmitancia_u: float = Field(..., description="Transmitancia térmica U en W/m²K")
    modo_obtencion: Literal["Defecto", "Estimado", "Conocido"] = "Defecto"
    longitud: Optional[float] = None
    altura: Optional[float] = None

class HuecoVentana(BaseModel):
    nombre: str
    orientacion: Literal["N", "S", "E", "O", "NE", "NO", "SE", "SO", "H"] = "N"
    superficie: float = Field(..., description="Superficie total del hueco en m²")
    transmitancia_u: float = Field(..., description="Transmitancia térmica U en W/m²K")
    factor_solar: float = Field(0.75, description="Factor solar modificador del vidrio g_perp")
    tipo_vidrio: str = "Doble estándar"
    tipo_marco: str = "Aluminio con RPT"
    permeabilidad: float = Field(50.0, description="Permeabilidad al aire en m³/h·m² a 100 Pa")

class InstalacionTermica(BaseModel):
    nombre: str
    tipo_servicio: Literal["Calefaccion", "Refrigeracion", "ACS", "Mixto2", "Mixto3"] = "ACS"
    tecnologia: Literal["CalderaEstandar", "CalderaCondensacion", "BombaCalorAerotermia", "EfectoJoule", "Biomasa"] = "EfectoJoule"
    vector_energetico: Literal["Electricidad", "GasNatural", "Gasoleo", "BiomasaPellet"] = "Electricidad"
    rendimiento_estacional: float = Field(1.0, description="Rendimiento estacional o SCOP/COP (ej. 1.0 para efecto Joule, 3.2 para aerotermia, 0.85 para caldera)")
    potencia_nominal_kw: float = Field(10.0, description="Potencia térmica nominal en kW")
    cobertura_pct: float = Field(100.0, description="Porcentaje de demanda que cubre este equipo")

class MedidaMejora(BaseModel):
    nombre: str
    tipo: Literal["Envolvente", "Instalaciones", "Renovables", "Conjunto"]
    descripcion: str
    inversion_estimada_eur: float
    ahorro_energia_primaria_pct: float
    ahorro_emisiones_pct: float
    ahorro_factura_anual_eur: float
    nueva_letra_emisiones: str
    nueva_letra_energia_primaria: str
    periodo_retorno_anos: float

class ProyectoCertificacion(BaseModel):
    administrativos: DatosAdministrativos
    generales: DatosGenerales
    opacos: List[CerramientoOpaco] = []
    huecos: List[HuecoVentana] = []
    instalaciones: List[InstalacionTermica] = []
    medidas_mejora: List[MedidaMejora] = []

class ResultadoCalificacion(BaseModel):
    demanda_calefaccion: float
    demanda_refrigeracion: float
    demanda_acs: float
    consumo_energia_primaria_nr: float
    emisiones_co2: float
    letra_global_emisiones: str
    letra_global_energia_primaria: str
    letra_calefaccion: str
    letra_refrigeracion: str
    letra_acs: str


