from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import logging
from email.message import EmailMessage
import os
from typing import Dict, Optional, TypedDict
from dotenv import load_dotenv
import aiosmtplib
import secrets
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from schemas import RecuperacionForm

load_dotenv()

logger = logging.getLogger("uvicorn")

router = APIRouter(tags=["recuperacion"])

def require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise RuntimeError(f"Variable de entorno requerida no configurada: {name}")
    return value


EMAIL_FROM = require_env("EMAIL_FROM")
SMTP_USER = require_env("SMTP_USER")
SMTP_PASS = require_env("SMTP_PASS")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.office365.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
FRONTEND_URL = require_env("FRONTEND_URL")
RESET_PATH = require_env("RESET_PATH")
RESET_TOKEN_SECRET = require_env("RESET_TOKEN_SECRET")
RESET_TOKEN_EXP_MINUTES = int(os.getenv("RESET_TOKEN_EXP_MINUTES", "15"))

serializer = URLSafeTimedSerializer(RESET_TOKEN_SECRET)


class RecuperacionPayload(TypedDict):
    email: str
    nonce: str


def generar_token_recuperacion(email: str) -> str:
    payload = {"email": email, "nonce": secrets.token_urlsafe(8)}
    return serializer.dumps(payload)


def generar_link_recuperacion(token: str) -> str:
    base = FRONTEND_URL.rstrip("/")
    path = RESET_PATH if RESET_PATH.startswith("/") else f"/{RESET_PATH}"
    return f"{base}{path}?token={token}"


def verificar_token_recuperacion(token: str) -> Optional[RecuperacionPayload]:
    """Verifica que el token sea válido y no haya expirado"""
    try:
        payload: RecuperacionPayload = serializer.loads(
            token, max_age=RESET_TOKEN_EXP_MINUTES * 60
        )
        return payload
    except SignatureExpired:
        return None
    except BadSignature:
        return None
    except Exception:
        return None


def generar_contenido_email_recuperacion(nombre: str, apellido: str, link: str) -> Dict[str, str]:
    asunto = "Solicitud de Reinicio de Contraseña"
    
    cuerpo = f"""
    <html>
        <body>
            <p>Hola {apellido} {nombre},</p>
            <p>Recibimos tu solicitud de reinicio de contraseña. Haz clic en el enlace para continuar:</p>
            <p><a href="{link}">Restablecer contraseña</a></p>
            <p>El enlace expira en {RESET_TOKEN_EXP_MINUTES} minutos.</p>
            <br>
            <p>Saludos,</p>
            <p>El equipo de Mortadela</p>
        </body>
    </html>
    """
    
    return {
        "asunto": asunto,
        "cuerpo": cuerpo
    }


async def enviar_email_recuperacion(destinatario: str, nombre: str, apellido: str) -> bool:
    if not all([EMAIL_FROM, SMTP_USER, SMTP_PASS]):
        logger.error("Error: Credenciales de email no configuradas.")
        return False

    assert EMAIL_FROM is not None
    assert SMTP_USER is not None
    assert SMTP_PASS is not None

    token = generar_token_recuperacion(destinatario)

    reset_link = generar_link_recuperacion(token)
    contenido = generar_contenido_email_recuperacion(nombre, apellido, reset_link)

    message = EmailMessage()
    message["Subject"] = contenido["asunto"]
    message["From"] = EMAIL_FROM
    message["To"] = destinatario
    
    message.set_content("Email en formato HTML - utilizar cliente con soporte para HTML")
    message.add_alternative(contenido["cuerpo"], subtype="html")
    
    try:
        async with aiosmtplib.SMTP(hostname=SMTP_HOST, port=SMTP_PORT, start_tls=True) as smtp:
            await smtp.login(SMTP_USER, SMTP_PASS)
            await smtp.sendmail(EMAIL_FROM, [destinatario], message.as_string())
        
        logger.info(f"Email de recuperación enviado exitosamente a {destinatario}")
        return True
        
    except Exception as e:
        logger.error(f"Error al enviar email de recuperación a {destinatario}: {e}")
        return False


@router.post("/recuperacion")
async def enviar_recuperacion(data: RecuperacionForm):
    try:
        exito = await enviar_email_recuperacion(
            destinatario=data.email,
            nombre=data.nombre,
            apellido=data.apellido
        )
        
        if exito:
            return JSONResponse(
                content={
                    "success": True,
                    "message": "Email de recuperación enviado exitosamente"
                },
                status_code=200
            )
        else:
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Error al enviar el email de recuperación"
                },
                status_code=500
            )
            
    except Exception as e:
        logger.error(f"Error en endpoint de recuperación: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": f"Error al procesar la solicitud: {str(e)}"
            },
            status_code=500
        )


@router.get("/verificar-token-recuperacion")
def verificar_token_endpoint(token: str = Query(...)):
    """Verifica que el token de recuperación sea válido"""
    payload = verificar_token_recuperacion(token)
    
    if payload is None:
        return JSONResponse(
            content={
                "success": False,
                "error": "Token inválido o expirado"
            },
            status_code=401
        )
    
    return JSONResponse(
        content={
            "success": True,
            "email": payload.get("email"),
            "message": "Token válido"
        },
        status_code=200
    )