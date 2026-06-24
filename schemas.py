from pydantic import BaseModel, EmailStr

class ReclamoForm(BaseModel):
    nombre: str
    apellido: str
    area: str
    reporte: str
    email: EmailStr

class RecuperacionForm(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr

class NuevoEncargadoForm(BaseModel):
    nombre: str
    apellido: str
    legajo: int