from typing import Dict, List, Optional
import os
import logging
import asyncio
from email.message import EmailMessage
from dotenv import load_dotenv
import aiosmtplib

load_dotenv()

logger = logging.getLogger("uvicorn")

EMAIL_FROM: Optional[str] = os.getenv("EMAIL_FROM")
SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
SMTP_PASS: Optional[str] = os.getenv("SMTP_PASS")
SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.office365.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
CC_EMAILS_FILE = "emails_list.txt"


def generar_contenido_email_nuevo_encargado(nombre: str, apellido: str, legajo: str) -> Dict[str, str]:
    asunto = "Nuevo Encargado - Verificación de Cuenta Requerida"
    
    cuerpo = f"""
    <html>
        <body>
            <h2>Notificación: Nuevo Encargado Asignado</h2>
            <p>Se generó o actualizó un usuario a encargado.</p>
            <p>Es necesario verificar que el mismo tenga cuenta.</p>
            <br>
            <p><strong>Nombre y Apellido:</strong> {nombre} {apellido}</p>
            <p><strong>Legajo:</strong> {legajo}</p>
        </body>
    </html>
    """
    
    return {
        "asunto": asunto,
        "cuerpo": cuerpo
    }

def obtener_emails_cc() -> List[str]:
    emails_cc: List[str] = []
    try:
        if os.path.exists(CC_EMAILS_FILE):
            with open(CC_EMAILS_FILE, "r", encoding="utf-8") as f:
                for linea in f:
                    email = linea.strip()
                    if email and not email.startswith("#") and "@" in email:
                        emails_cc.append(email)
            logger.info(f"✓ Se cargaron {len(emails_cc)} emails de CC desde {CC_EMAILS_FILE}")
    except Exception as e:
        logger.error(f"Error leyendo emails de CC: {e}")
    
    return emails_cc

def validar_configuracion_smtp() -> bool:
    if not all([EMAIL_FROM, SMTP_USER, SMTP_PASS]):
        logger.error("Error: Credenciales de email no configuradas (EMAIL_FROM, SMTP_USER o SMTP_PASS faltantes).")
        return False
    return True

def validar_email(email: str) -> bool:
    return bool(email and "@" in email)

async def enviar_email(
    destinatario: str, 
    asunto: str, 
    cuerpo_html: str,
    cc_list: Optional[List[str]] = None,
    max_retries: int = 2
) -> bool:
    if not validar_configuracion_smtp():
        return False
    
    if not validar_email(destinatario):
        logger.error(f"Email destino inválido: {destinatario}")
        return False
    
    if cc_list is None:
        cc_list = []
    
    cc_list = [email for email in cc_list if validar_email(email)]
    
    todos_destinatarios = [destinatario] + cc_list
    
    logger.info(f"Preparando envío de email a {destinatario} con {len(cc_list)} en CC")
    
    message = EmailMessage()
    message["Subject"] = asunto
    message["From"] = EMAIL_FROM
    message["To"] = destinatario
    
    if cc_list:
        message["Cc"] = ", ".join(cc_list)
    
    message.set_content("Email en formato HTML - utilizar cliente con soporte para HTML")
    message.add_alternative(cuerpo_html, subtype="html")
    
    assert EMAIL_FROM is not None
    assert SMTP_USER is not None
    assert SMTP_PASS is not None
    
    for intento in range(max_retries):
        try:
            async with aiosmtplib.SMTP(hostname=SMTP_HOST, port=SMTP_PORT, start_tls=True) as smtp:
                await smtp.login(SMTP_USER, SMTP_PASS)
                await smtp.sendmail(EMAIL_FROM, todos_destinatarios, message.as_string())
            
            logger.info(f"✓ Email enviado exitosamente a {destinatario} (intento {intento + 1}/{max_retries})")
            return True
            
        except Exception as e:
            logger.warning(f"Intento {intento + 1}/{max_retries} fallido para {destinatario}: {e}")
            
            if intento < max_retries - 1:
                await asyncio.sleep(2 ** intento)
            else:
                logger.error(f"Error final al enviar email a {destinatario}: {e}")
                return False
    
    return False


class EmailServiceNotificar:
    @staticmethod
    def generar_contenido_email_nuevo_encargado(nombre: str, apellido: str, legajo: str) -> Dict[str, str]:
        return generar_contenido_email_nuevo_encargado(nombre, apellido, legajo)
    
    @staticmethod
    def obtener_emails_cc() -> List[str]:
        return obtener_emails_cc()
    
    @staticmethod
    async def enviar_email(
        destinatario: str, 
        asunto: str, 
        cuerpo_html: str,
        cc_list: Optional[List[str]] = None
    ) -> bool:
        return await enviar_email(destinatario, asunto, cuerpo_html, cc_list)
