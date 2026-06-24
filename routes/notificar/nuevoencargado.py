from typing import Dict, Any
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from schemas import NuevoEncargadoForm
from routes.notificar.email import EmailServiceNotificar
import logging

logger = logging.getLogger("uvicorn")

router = APIRouter(prefix="/notificar", tags=["notificar"])

@router.post("/nuevo-encargado", status_code=status.HTTP_201_CREATED)
async def notificar_nuevo_encargado(datos: NuevoEncargadoForm) -> Dict[str, Any]:
    """
    Recibe datos de un nuevo encargado desde otra API y notifica a sistemas@creminox.com
    
    Args:
        datos: NuevoEncargadoForm con nombre, apellido y legajo
    
    Returns:
        JSON con estado del envío del email
    """
    
    contenido = EmailServiceNotificar.generar_contenido_email_nuevo_encargado(
        datos.nombre,
        datos.apellido,
        datos.legajo
    )
    
    cc_emails = EmailServiceNotificar.obtener_emails_cc()
    
    email_enviado = await EmailServiceNotificar.enviar_email(
        "sistemas@creminox.com",
        contenido["asunto"],
        contenido["cuerpo"],
        cc_emails
    )
    
    if email_enviado:
        logger.info(f"✓ Notificación de nuevo encargado enviada: {datos.nombre} {datos.apellido} (Legajo: {datos.legajo})")
        return {
            "success": True,
            "mensaje": "Notificación enviada exitosamente a sistemas@creminox.com",
            "datos": {
                "nombre": datos.nombre,
                "apellido": datos.apellido,
                "legajo": datos.legajo
            }
        }
    else:
        logger.error(f"Error al enviar notificación de nuevo encargado: {datos.nombre} {datos.apellido}")
        return JSONResponse(
            content={
                "success": False,
                "error": "Error al enviar la notificación por email"
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
