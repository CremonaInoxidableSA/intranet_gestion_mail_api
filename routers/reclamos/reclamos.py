from typing import Dict, Any
from fastapi import APIRouter, status
from schemas import ReclamoForm
from routers.reclamos.email import EmailService

router = APIRouter(prefix="/reclamos", tags=["reclamos"])

@router.post("/crear", status_code=status.HTTP_201_CREATED)
async def crear_reclamo(reclamo: ReclamoForm) -> Dict[str, Any]:
    contenido = EmailService.generar_contenido_email(
        reclamo.nombre,
        reclamo.apellido,
        reclamo.area,
        reclamo.reporte
    )
    
    cc_emails = EmailService.obtener_emails_cc()
    
    cc_emails.append(reclamo.email)
    
    email_enviado = await EmailService.enviar_email(
        "sistemas@creminox.com",
        contenido["asunto"],
        contenido["cuerpo"],
        cc_emails
    )
    
    return {
        "enviado": email_enviado,
        "email_destino": "sistemas@creminox.com",
        "cantidad_cc": len(cc_emails)
    }