from typing import Dict, Any
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from schemas import ReclamoForm
from routes.reclamos.email import EmailService
from config.db import SessionLocal, Antispam
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("uvicorn")

router = APIRouter(prefix="/reclamos", tags=["reclamos"])

@router.post("/crear", status_code=status.HTTP_201_CREATED)
async def crear_reclamo(reclamo: ReclamoForm) -> Dict[str, Any]:
    # Verificar si existe un registro en antispam para este correo en los últimos 30 minutos
    try:
        db = SessionLocal()
        hace_30_minutos = datetime.utcnow() - timedelta(minutes=30)
        
        registro_reciente = db.query(Antispam).filter(
            Antispam.correo == reclamo.email,
            Antispam.fecha > hace_30_minutos
        ).first()
        
        db.close()
        
        if registro_reciente:
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Ya existe un reclamo reciente para este correo. Por favor espera 30 minutos antes de enviar otro."
                },
                status_code=429
            )
    except Exception as e:
        logger.error(f"Error al verificar antispam: {e}")
    
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
    
    # Si el email se envió exitosamente, registrar en la tabla antispam
    if email_enviado:
        try:
            db = SessionLocal()
            nuevo_registro = Antispam(
                accion="reclamo",
                fecha=datetime.utcnow(),
                correo=reclamo.email
            )
            db.add(nuevo_registro)
            db.commit()
            db.close()
            logger.info(f"✓ Registro antispam creado para {reclamo.email}")
        except Exception as e:
            logger.error(f"Error al registrar en antispam: {e}")
    
    return {
        "enviado": email_enviado,
        "email_destino": "sistemas@creminox.com"
    }