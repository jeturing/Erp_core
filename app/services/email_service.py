"""
Email Transactional Service — SMTP (ipzmarketing/mailrelay)
Envía correos transaccionales: credenciales, facturas, notificaciones.
"""
import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict, Any

from ..config import (
    APP_URL,
    SMTP_ENCRYPTION,
    SMTP_FROM_EMAIL,
    SMTP_FROM_NAME,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_SERVER,
    SMTP_USER,
    smtp_is_configured,
)

logger = logging.getLogger(__name__)

def _get_smtp_connection():
    """Crea conexión SMTP usando únicamente la configuración centralizada."""
    if not smtp_is_configured():
        raise RuntimeError("SMTP no configurado en el .env activo")

    if SMTP_ENCRYPTION == "STARTTLS" or SMTP_PORT == 587:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
        server.ehlo()
        server.starttls()
        server.ehlo()
    else:
        # SSL/TLS por defecto (puerto 465)
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30)
    
    server.login(SMTP_USER, SMTP_PASSWORD)
    return server


def _log_to_db(
    recipient: str,
    subject: str,
    email_type: str,
    status: str,
    error_message: Optional[str] = None,
    customer_id: Optional[int] = None,
    partner_id: Optional[int] = None,
    related_id: Optional[int] = None,
):
    """Persiste el registro del email en la tabla email_logs."""
    try:
        from ..models.database import EmailLog, SessionLocal
        from datetime import datetime
        db = SessionLocal()
        try:
            record = EmailLog(
                recipient=recipient,
                subject=subject,
                email_type=email_type,
                status=status,
                error_message=error_message,
                customer_id=customer_id,
                partner_id=partner_id,
                related_id=related_id,
                sent_at=datetime.utcnow(),
            )
            db.add(record)
            db.commit()
        except Exception as db_err:
            db.rollback()
            logger.warning(f"Could not log email to DB: {db_err}")
        finally:
            db.close()
    except Exception:
        pass  # Never let logging break the send flow


def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
    reply_to: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    email_type: str = "generic",
    customer_id: Optional[int] = None,
    partner_id: Optional[int] = None,
    related_id: Optional[int] = None,
) -> dict:
    """
    Envía un email transaccional y lo registra en email_logs.

    Returns:
        {"success": True/False, "message_id": str, "error": str}
    """
    try:
        if not smtp_is_configured():
            raise RuntimeError("SMTP no configurado en el .env activo")

        msg = MIMEMultipart("mixed")
        msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        if reply_to:
            msg["Reply-To"] = reply_to

        # Cuerpo del correo (plain + html)
        body = MIMEMultipart("alternative")
        if text_body:
            body.attach(MIMEText(text_body, "plain", "utf-8"))

        body.attach(MIMEText(html_body, "html", "utf-8"))
        msg.attach(body)

        # Adjuntos opcionales
        if attachments:
            for attachment in attachments:
                path = attachment.get("path")
                filename = attachment.get("filename") or (os.path.basename(path) if path else None)
                mime_type = attachment.get("mime_type", "application/octet-stream")
                content = attachment.get("content")

                if content is None:
                    if not path:
                        raise ValueError("Adjunto inválido: falta 'path' o 'content'")
                    with open(path, "rb") as f:
                        content = f.read()

                main_type, sub_type = mime_type.split("/", 1) if "/" in mime_type else ("application", "octet-stream")
                part = MIMEBase(main_type, sub_type)
                part.set_payload(content)
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f'attachment; filename="{filename or "adjunto.bin"}"')
                msg.attach(part)

        server = _get_smtp_connection()
        server.sendmail(SMTP_FROM_EMAIL, to_email, msg.as_string())
        server.quit()

        logger.info(f"✅ Email enviado a {to_email}: {subject}")
        _log_to_db(to_email, subject, email_type, "sent", customer_id=customer_id, partner_id=partner_id, related_id=related_id)
        return {"success": True, "to": to_email, "subject": subject}

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Error SMTP auth: {e}")
        _log_to_db(to_email, subject, email_type, "failed", error_message=str(e), customer_id=customer_id, partner_id=partner_id, related_id=related_id)
        return {"success": False, "error": f"Error de autenticación SMTP: {e}"}
    except Exception as e:
        logger.error(f"Error enviando email a {to_email}: {e}")
        _log_to_db(to_email, subject, email_type, "failed", error_message=str(e), customer_id=customer_id, partner_id=partner_id, related_id=related_id)
        return {"success": False, "error": str(e)}


# ────────────────────────────────────────────
# Templates de emails transaccionales
# ────────────────────────────────────────────

def _base_template(content: str) -> str:
    """Wrapper HTML base con estilo SAJET"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                 background: #1a1a2e; color: #e0e0e0; padding: 40px 20px; margin: 0;">
      <div style="max-width: 600px; margin: 0 auto; background: #16213e; border-radius: 12px; 
                  border: 1px solid #2a2a4a; overflow: hidden;">
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #c0392b, #e74c3c); padding: 24px 32px;">
          <h1 style="margin: 0; color: #fff; font-size: 24px; font-weight: 700;">SAJET</h1>
          <p style="margin: 4px 0 0; color: rgba(255,255,255,0.8); font-size: 13px;">Enterprise Platform</p>
        </div>
        <!-- Content -->
        <div style="padding: 32px;">
          {content}
        </div>
        <!-- Footer -->
        <div style="padding: 16px 32px; background: #0f1629; text-align: center; font-size: 12px; color: #666;">
          <p style="margin: 0;">© 2026 Jeturing SRL — SAJET Platform</p>
          <p style="margin: 4px 0 0;">Este es un mensaje automático, no responda a este correo.</p>
        </div>
      </div>
    </body>
    </html>
    """


def send_tenant_credentials(
    to_email: str,
    company_name: str,
    subdomain: str,
    admin_login: str,
    admin_password: str,
    plan_name: str = "basic",
) -> dict:
    """Envía credenciales de acceso al tenant nuevo"""
    url = f"https://{subdomain}.sajet.us"
    portal_url = f"{APP_URL}/tenant/portal"

    content = f"""
    <h2 style="color: #e74c3c; margin-top: 0;">¡Bienvenido a SAJET! 🎉</h2>
    <p>Hola, su cuenta para <strong>{company_name}</strong> ha sido creada exitosamente.</p>
    
    <div style="background: #1a1a2e; border-radius: 8px; padding: 20px; margin: 20px 0; 
                border-left: 4px solid #e74c3c;">
      <h3 style="margin-top: 0; color: #fff;">Datos de acceso a Odoo</h3>
      <table style="width: 100%; border-collapse: collapse;">
        <tr><td style="padding: 6px 0; color: #999;">URL:</td>
            <td style="padding: 6px 0;"><a href="{url}" style="color: #e74c3c;">{url}</a></td></tr>
        <tr><td style="padding: 6px 0; color: #999;">Usuario:</td>
            <td style="padding: 6px 0; font-family: monospace;">{admin_login}</td></tr>
        <tr><td style="padding: 6px 0; color: #999;">Contraseña:</td>
            <td style="padding: 6px 0; font-family: monospace; background: #2a2a4a; padding: 4px 8px; 
                        border-radius: 4px;">{admin_password}</td></tr>
        <tr><td style="padding: 6px 0; color: #999;">Plan:</td>
            <td style="padding: 6px 0; text-transform: capitalize;">{plan_name}</td></tr>
      </table>
    </div>

    <div style="background: #1a1a2e; border-radius: 8px; padding: 20px; margin: 20px 0;
                border-left: 4px solid #3498db;">
      <h3 style="margin-top: 0; color: #fff;">Portal de Cliente</h3>
      <p>Gestione su suscripción, facturación y dominios desde:</p>
      <a href="{portal_url}" style="display: inline-block; background: #e74c3c; color: #fff; 
         padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600;">
        Acceder al Portal →
      </a>
    </div>

    <p style="color: #999; font-size: 13px;">
      ⚠️ Por seguridad, cambie su contraseña después del primer inicio de sesión.
    </p>
    """

    return send_email(
        to_email=to_email,
        subject=f"🔑 Credenciales de acceso — {company_name} | SAJET",
        html_body=_base_template(content),
        text_body=f"Bienvenido a SAJET\n\nURL: {url}\nUsuario: {admin_login}\nContraseña: {admin_password}\nPlan: {plan_name}",
        email_type="tenant_credentials",
    )


def _partner_template(content: str, brand: dict) -> str:
    """
    Wrapper HTML con branding del partner.
    `brand` puede tener: brand_name, brand_color_primary, brand_color_accent, logo_url.
    Si los campos están vacíos se usan los defaults de SAJET.
    """
    name    = brand.get("brand_name") or "SAJET"
    color1  = brand.get("brand_color_primary") or "#c0392b"
    color2  = brand.get("brand_color_accent")  or "#e74c3c"
    logo    = brand.get("logo_url") or ""

    logo_html = (
        f'<img src="{logo}" alt="{name}" style="max-height:48px;max-width:180px;'
        f'display:block;margin-bottom:6px;" />'
        if logo else
        f'<h1 style="margin:0;color:#fff;font-size:24px;font-weight:700;">{name}</h1>'
    )

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                 background: #1a1a2e; color: #e0e0e0; padding: 40px 20px; margin: 0;">
      <div style="max-width: 600px; margin: 0 auto; background: #16213e; border-radius: 12px;
                  border: 1px solid #2a2a4a; overflow: hidden;">
        <!-- Header con branding del partner -->
        <div style="background: linear-gradient(135deg, {color1}, {color2}); padding: 24px 32px;">
          {logo_html}
          <p style="margin: 4px 0 0; color: rgba(255,255,255,0.8); font-size: 13px;">Powered by SAJET Platform</p>
        </div>
        <!-- Content -->
        <div style="padding: 32px;">
          {content}
        </div>
        <!-- Footer -->
        <div style="padding: 16px 32px; background: #0f1629; text-align: center; font-size: 12px; color: #666;">
          <p style="margin: 0;">{name} — Powered by <strong>SAJET</strong></p>
          <p style="margin: 4px 0 0;">Este es un mensaje automático, no responda a este correo.</p>
        </div>
      </div>
    </body>
    </html>
    """


def send_tenant_welcome(
    to_email: str,
    company_name: str,
    subdomain: str,
    plan_name: str,
    admin_login: str,
    admin_password: str,
    client_login: str,
    client_password: str,
    partner_login: Optional[str] = None,
    partner_password: Optional[str] = None,
    customer_id: Optional[int] = None,
    # Branding del partner (si el tenant fue provisionado por un socio)
    partner_brand: Optional[dict] = None,
) -> dict:
    """
    Email de bienvenida con las 3 credenciales del tenant:
      1. Administrador Odoo  — backend ERP completo
      2. Usuario cliente     — portal Sajet (suscripción/facturación)
      3. Partner/Reseller    — panel partner (opcional)

    Si se pasa `partner_brand` (dict con brand_name, brand_color_primary,
    brand_color_accent, logo_url, smtp_from_name, smtp_from_email),
    el email se envía con el branding del partner en lugar del de SAJET.
    """
    url        = f"https://{subdomain}.sajet.us"
    portal_url = f"{APP_URL}/tenant/portal"

    # Determinar si hay branding de partner
    use_partner_brand = bool(partner_brand and any(partner_brand.values()))
    brand = partner_brand or {}

    # From personalizado del partner (o default SAJET)
    from_name  = brand.get("smtp_from_name")  or SMTP_FROM_NAME
    from_email = brand.get("smtp_from_email") or SMTP_FROM_EMAIL

    accent_admin  = brand.get("brand_color_primary") or "#e74c3c"
    accent_client = brand.get("brand_color_accent")  or "#3498db"

    def _row(label, value):
        return (
            f'<tr>'
            f'<td style="padding:6px 0;color:#999;width:130px;vertical-align:top;">{label}</td>'
            f'<td style="padding:6px 0;font-family:monospace;background:#2a2a4a;'
            f'padding:4px 10px;border-radius:4px;">{value}</td>'
            f'</tr>'
        )

    partner_block = ""
    if partner_login and partner_password:
        partner_block = f"""
    <div style="background:#1a1a2e;border-radius:8px;padding:20px;margin:20px 0;
                border-left:4px solid #9b59b6;">
      <h3 style="margin-top:0;color:#fff;">👤 Partner / Reseller</h3>
      <p style="color:#aaa;font-size:13px;margin-top:0;">Acceso al portal de socio.</p>
      <table style="width:100%;border-collapse:collapse;">
        {_row("Portal:", f'<a href="{APP_URL}/partner" style="color:#9b59b6;">{APP_URL}/partner</a>')}
        {_row("Usuario:", partner_login)}
        {_row("Contraseña:", partner_password)}
      </table>
    </div>"""

    content = f"""
    <h2 style="color:{accent_admin};margin-top:0;">¡Bienvenido! 🎉</h2>
    <p>El tenant de <strong>{company_name}</strong> fue creado exitosamente — plan <strong>{plan_name}</strong>.</p>
    <p style="color:#aaa;font-size:13px;">A continuación encontrará las credenciales de acceso para cada perfil.</p>

    <div style="background:#1a1a2e;border-radius:8px;padding:20px;margin:20px 0;
                border-left:4px solid {accent_admin};">
      <h3 style="margin-top:0;color:#fff;">🔧 Administrador Odoo (ERP)</h3>
      <p style="color:#aaa;font-size:13px;margin-top:0;">Acceso completo al backend del sistema.</p>
      <table style="width:100%;border-collapse:collapse;">
        {_row("URL:", f'<a href="{url}" style="color:{accent_admin};">{url}</a>')}
        {_row("Usuario:", admin_login)}
        {_row("Contraseña:", admin_password)}
      </table>
    </div>

    <div style="background:#1a1a2e;border-radius:8px;padding:20px;margin:20px 0;
                border-left:4px solid {accent_client};">
      <h3 style="margin-top:0;color:#fff;">🌐 Cliente (Portal SAJET)</h3>
      <p style="color:#aaa;font-size:13px;margin-top:0;">Gestión de suscripción, facturación y soporte.</p>
      <table style="width:100%;border-collapse:collapse;">
        {_row("Portal:", f'<a href="{portal_url}" style="color:{accent_client};">{portal_url}</a>')}
        {_row("Usuario:", client_login)}
        {_row("Contraseña:", client_password)}
      </table>
    </div>

    {partner_block}

    <p style="color:#f39c12;font-size:13px;">⚠️ Por seguridad, cambie las contraseñas tras el primer inicio de sesión.</p>
    <p style="color:#999;font-size:12px;">Soporte: <a href="mailto:soporte@sajet.us" style="color:{accent_admin};">soporte@sajet.us</a></p>
    """

    text = (
        f"Bienvenido — {company_name}\n\n"
        f"=== Administrador Odoo ===\n"
        f"URL: {url}\nUsuario: {admin_login}\nContraseña: {admin_password}\n\n"
        f"=== Cliente Portal SAJET ===\n"
        f"Portal: {portal_url}\nUsuario: {client_login}\nContraseña: {client_password}\n"
    )
    if partner_login and partner_password:
        text += (
            f"\n=== Partner ===\n"
            f"Portal: {APP_URL}/partner\nUsuario: {partner_login}\nContraseña: {partner_password}\n"
        )

    html_body = _partner_template(content, brand) if use_partner_brand else _base_template(content)

    # Construir mensaje con From personalizado del partner si aplica
    if use_partner_brand and brand.get("smtp_from_email"):
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText as _MIMEText
            msg = MIMEMultipart("alternative")
            msg["From"]    = f"{from_name} <{from_email}>"
            msg["To"]      = to_email
            msg["Subject"] = f"🔑 Credenciales de acceso — {company_name}"
            if text:
                msg.attach(_MIMEText(text, "plain", "utf-8"))
            msg.attach(_MIMEText(html_body, "html", "utf-8"))
            smtp_conn = _get_smtp_connection()
            smtp_conn.sendmail(from_email, to_email, msg.as_string())
            smtp_conn.quit()
            logger.info(f"✅ Email bienvenida (partner brand) enviado a {to_email}")
            _log_to_db(to_email, f"Credenciales — {company_name}", "tenant_welcome",
                       "sent", customer_id=customer_id)
            return {"success": True, "to": to_email}
        except Exception as e:
            logger.warning(f"⚠️ Error enviando con From del partner, reintentando con SAJET SMTP: {e}")
            # fallback → usa el SMTP de SAJET normal

    return send_email(
        to_email=to_email,
        subject=f"🔑 Credenciales de acceso — {company_name}",
        html_body=html_body,
        text_body=text,
        email_type="tenant_welcome",
        customer_id=customer_id,
    )


def send_password_reset(
    to_email: str,
    company_name: str,
    subdomain: str,
    new_password: str,
) -> dict:
    """Envía email con nueva contraseña reseteada"""
    url = f"https://{subdomain}.sajet.us"

    content = f"""
    <h2 style="color: #e74c3c; margin-top: 0;">Contraseña restablecida 🔒</h2>
    <p>Se ha restablecido la contraseña para la cuenta de <strong>{company_name}</strong>.</p>
    
    <div style="background: #1a1a2e; border-radius: 8px; padding: 20px; margin: 20px 0;
                border-left: 4px solid #f39c12;">
      <h3 style="margin-top: 0; color: #fff;">Nueva contraseña</h3>
      <p style="font-family: monospace; font-size: 18px; background: #2a2a4a; 
                padding: 12px 16px; border-radius: 6px; display: inline-block;">
        {new_password}
      </p>
      <p style="margin-bottom: 0;">
        <a href="{url}" style="color: #e74c3c;">Iniciar sesión →</a>
      </p>
    </div>

    <p style="color: #999; font-size: 13px;">
      ⚠️ Cambie esta contraseña temporal después de iniciar sesión.
    </p>
    """

    return send_email(
        to_email=to_email,
        subject=f"🔒 Contraseña restablecida — {company_name} | SAJET",
        html_body=_base_template(content),
        text_body=f"Contraseña restablecida\n\nURL: {url}\nNueva contraseña: {new_password}",
        email_type="password_reset",
    )


def send_tenant_backup_deleted(
    to_email: str,
    company_name: str,
    subdomain: str,
    backup_path: str,
    backup_filename: Optional[str] = None,
) -> dict:
    """Envía al cliente el backup de su tenant al momento de la eliminación."""
    file_name = backup_filename or os.path.basename(backup_path)
    content = f"""
    <h2 style="color: #e74c3c; margin-top: 0;">Tenant eliminado con respaldo</h2>
    <p>Hola, se completó la eliminación del tenant <strong>{subdomain}</strong> ({company_name}).</p>
    <p>Adjuntamos el respaldo de la base de datos para su archivo.</p>

    <div style="background: #1a1a2e; border-radius: 8px; padding: 20px; margin: 20px 0; 
                border-left: 4px solid #3498db;">
      <h3 style="margin-top: 0; color: #fff;">Detalle del respaldo</h3>
      <p style="margin: 4px 0;"><strong>Archivo:</strong> {file_name}</p>
      <p style="margin: 4px 0;"><strong>Tenant:</strong> {subdomain}</p>
    </div>

    <p style="color: #999; font-size: 13px;">
      Si no solicitó esta acción, contacte soporte inmediatamente.
    </p>
    """

    return send_email(
        to_email=to_email,
        subject=f"📦 Backup tenant eliminado — {subdomain} | SAJET",
        html_body=_base_template(content),
        text_body=f"Tenant eliminado: {subdomain}\nArchivo backup: {file_name}",
        attachments=[
            {
                "path": backup_path,
                "filename": file_name,
                "mime_type": "application/octet-stream",
            }
        ],
        email_type="tenant_backup_deleted",
    )


def send_commission_notification(
    to_email: str,
    partner_name: str,
    period: str,
    gross_revenue: float,
    net_revenue: float,
    partner_amount: float,
    status: str = "approved",
) -> dict:
    """Notifica al partner sobre una comisión aprobada/pagada"""
    status_label = "aprobada ✅" if status == "approved" else "pagada 💰"

    content = f"""
    <h2 style="color: #e74c3c; margin-top: 0;">Comisión {status_label}</h2>
    <p>Hola <strong>{partner_name}</strong>, su comisión del período <strong>{period}</strong> ha sido {status_label}.</p>
    
    <div style="background: #1a1a2e; border-radius: 8px; padding: 20px; margin: 20px 0;
                border-left: 4px solid #2ecc71;">
      <table style="width: 100%; border-collapse: collapse;">
        <tr><td style="padding: 8px 0; color: #999;">Ingreso bruto:</td>
            <td style="padding: 8px 0; text-align: right;">${gross_revenue:,.2f}</td></tr>
        <tr><td style="padding: 8px 0; color: #999;">Ingreso neto:</td>
            <td style="padding: 8px 0; text-align: right;">${net_revenue:,.2f}</td></tr>
        <tr style="border-top: 1px solid #2a2a4a;">
            <td style="padding: 12px 0; color: #fff; font-weight: 600;">Su comisión (50%):</td>
            <td style="padding: 12px 0; text-align: right; color: #2ecc71; font-size: 20px; font-weight: 700;">
                ${partner_amount:,.2f}</td></tr>
      </table>
    </div>
    """

    return send_email(
        to_email=to_email,
        subject=f"💰 Comisión {status_label} — {period} | SAJET",
        html_body=_base_template(content),
        text_body=f"Comisión {status_label}\nPeríodo: {period}\nMonto: ${partner_amount:,.2f}",
        email_type="commission_notification",
    )


def send_quotation_email(
    to_email: str,
    prospect_name: str,
    quote_number: str,
    total_monthly: float,
    lines_summary: str,
    valid_until: str = "",
    notes: str = "",
) -> dict:
    """Envía cotización por email"""
    content = f"""
    <h2 style="color: #e74c3c; margin-top: 0;">Cotización {quote_number}</h2>
    <p>Estimado/a <strong>{prospect_name}</strong>,</p>
    <p>Adjunto encontrará nuestra propuesta de servicios:</p>

    <div style="background: #1a1a2e; border-radius: 8px; padding: 20px; margin: 20px 0;
                border-left: 4px solid #e74c3c;">
      {lines_summary}
      <hr style="border-color: #2a2a4a; margin: 16px 0;">
      <p style="text-align: right; font-size: 20px; color: #e74c3c; font-weight: 700; margin: 0;">
        Total mensual: ${total_monthly:,.2f} USD
      </p>
    </div>

    {"<p style='color: #999;'>Válido hasta: " + valid_until + "</p>" if valid_until else ""}
    {"<p style='color: #999;'>" + notes + "</p>" if notes else ""}

    <p>Para aceptar esta cotización o si tiene preguntas, responda a este correo.</p>
    """

    return send_email(
        to_email=to_email,
        subject=f"📋 Cotización {quote_number} — SAJET",
        html_body=_base_template(content),
        text_body=f"Cotización {quote_number}\nTotal: ${total_monthly:,.2f}/mes",
        reply_to="ventas@sajet.us",
        email_type="quotation",
    )


def send_partner_change_notification(
    to_email: str,
    company_name: str,
    old_partner_name: Optional[str] = None,
    new_partner_name: Optional[str] = None,
    action: str = "transfer",
) -> dict:
    """
    Notifica al cliente sobre un cambio en su partner de soporte/facturación.
    action: 'transfer' (cambio de partner), 'link' (nuevo partner asignado), 'unlink' (desvinculado)
    """
    if action == "unlink":
        title = "Cambio en su cuenta — Partner desvinculado"
        emoji = "🔄"
        main_text = (
            f"<p>Le informamos que su cuenta de <strong>{company_name}</strong> "
            f"ha sido desvinculada del partner <strong>{old_partner_name}</strong>.</p>"
            f"<p>A partir de ahora, su facturación y soporte serán gestionados directamente por <strong>SAJET / Jeturing SRL</strong>.</p>"
        )
    elif action == "link":
        title = "¡Nuevo partner asignado!"
        emoji = "🤝"
        main_text = (
            f"<p>Le informamos que su cuenta de <strong>{company_name}</strong> "
            f"ha sido vinculada al partner <strong>{new_partner_name}</strong>.</p>"
            f"<p>Su facturación y soporte técnico serán gestionados a través de este partner.</p>"
        )
    else:  # transfer
        title = "Cambio de partner en su cuenta"
        emoji = "🔄"
        from_text = f" de <strong>{old_partner_name}</strong>" if old_partner_name else ""
        main_text = (
            f"<p>Le informamos que su cuenta de <strong>{company_name}</strong> "
            f"ha sido transferida{from_text} al partner <strong>{new_partner_name}</strong>.</p>"
            f"<p>A partir de ahora, su facturación y soporte serán gestionados por <strong>{new_partner_name}</strong>.</p>"
        )

    content = f"""
    <h2 style="color: #e74c3c; margin-top: 0;">{title} {emoji}</h2>
    {main_text}

    <div style="background: #1a1a2e; border-radius: 8px; padding: 20px; margin: 20px 0;
                border-left: 4px solid #3498db;">
      <h3 style="margin-top: 0; color: #fff; font-size: 14px;">¿Qué significa esto?</h3>
      <ul style="color: #ccc; font-size: 13px; margin: 0; padding-left: 20px;">
        <li>Su servicio y datos no se ven afectados</li>
        <li>Su acceso a la plataforma continúa sin cambios</li>
        <li>Las facturas futuras reflejarán el nuevo esquema</li>
      </ul>
    </div>

    <p style="color: #999; font-size: 13px;">
      Si tiene preguntas sobre este cambio, por favor contacte a su equipo de soporte.
    </p>

    <a href="{APP_URL}/#/portal" style="display: inline-block; background: #e74c3c; color: #fff;
       padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600; margin-top: 10px;">
      Ir al Portal →
    </a>
    """

    return send_email(
        to_email=to_email,
        subject=f"{emoji} {title} — {company_name} | SAJET",
        html_body=_base_template(content),
        text_body=f"{title}\nEmpresa: {company_name}\n"
                  f"{'Anterior: ' + old_partner_name if old_partner_name else ''}\n"
                  f"{'Nuevo: ' + new_partner_name if new_partner_name else 'Gestión directa SAJET'}",
        email_type="partner_change",
    )

def send_work_order_completion(
    to_email: str,
    company_name: str,
    subdomain: str,
    admin_login: str,
    admin_password: str,
    user_login: str,
    user_password: str,
    approved_modules: list,
    order_number: str,
) -> dict:
    """
    Envía credenciales de acceso al completar una work order de aprovisionamiento.
    Sin referencias a Odoo — texto neutro de plataforma.
    """
    url = f"https://{subdomain}.sajet.us" if subdomain else APP_URL
    portal_url = f"{APP_URL}/#/portal"

    modules_html = ""
    if approved_modules:
        items = "".join(
            f"<li style='color:#ccc;margin:3px 0;font-size:13px;'>{m}</li>"
            for m in approved_modules[:25]
        )
        extra = f"<li style='color:#666;'>... y {len(approved_modules)-25} más</li>" if len(approved_modules) > 25 else ""
        modules_html = f"""
    <div style="background:#1a1a2e;border-radius:8px;padding:16px;margin:16px 0;border-left:4px solid #3498db;">
      <h3 style="margin-top:0;color:#fff;font-size:14px;">✅ Aplicaciones configuradas ({len(approved_modules)})</h3>
      <ul style="margin:0;padding-left:20px;">{items}{extra}</ul>
    </div>"""

    content = f"""
    <h2 style="color:#e74c3c;margin-top:0;">¡Su espacio de trabajo está listo! 🎉</h2>
    <p>El espacio de trabajo para <strong>{company_name}</strong> ha sido configurado y está disponible.</p>
    <p style="color:#999;font-size:12px;">Referencia de orden: <code style="background:#2a2a4a;padding:2px 6px;border-radius:3px;">{order_number}</code></p>

    <div style="background:#1a1a2e;border-radius:8px;padding:20px;margin:20px 0;border-left:4px solid #e74c3c;">
      <h3 style="margin-top:0;color:#fff;font-size:15px;">🔑 Acceso de Administrador</h3>
      <p style="color:#999;font-size:12px;margin-bottom:12px;">Use estas credenciales para la configuración inicial del sistema.</p>
      <table style="width:100%;border-collapse:collapse;">
        <tr><td style="padding:6px 0;color:#999;width:100px;">URL:</td>
            <td style="padding:6px 0;"><a href="{url}" style="color:#e74c3c;font-weight:600;">{url}</a></td></tr>
        <tr><td style="padding:6px 0;color:#999;">Usuario:</td>
            <td style="padding:6px 0;font-family:monospace;font-size:14px;">{admin_login}</td></tr>
        <tr><td style="padding:6px 0;color:#999;">Contraseña:</td>
            <td style="padding:6px 0;"><code style="background:#2a2a4a;padding:3px 8px;border-radius:4px;font-size:14px;">{admin_password}</code></td></tr>
      </table>
    </div>

    <div style="background:#1a1a2e;border-radius:8px;padding:20px;margin:20px 0;border-left:4px solid #2ecc71;">
      <h3 style="margin-top:0;color:#fff;font-size:15px;">👤 Su acceso de usuario</h3>
      <p style="color:#999;font-size:12px;margin-bottom:12px;">Este usuario tiene acceso a las aplicaciones de su cuenta (sin módulo de administración del sistema).</p>
      <table style="width:100%;border-collapse:collapse;">
        <tr><td style="padding:6px 0;color:#999;width:100px;">Usuario:</td>
            <td style="padding:6px 0;font-family:monospace;font-size:14px;">{user_login}</td></tr>
        <tr><td style="padding:6px 0;color:#999;">Contraseña:</td>
            <td style="padding:6px 0;"><code style="background:#2a2a4a;padding:3px 8px;border-radius:4px;font-size:14px;">{user_password}</code></td></tr>
      </table>
    </div>

    {modules_html}

    <div style="background:#1a1a2e;border-radius:8px;padding:16px;margin:16px 0;border-left:4px solid #9b59b6;">
      <h3 style="margin-top:0;color:#fff;font-size:14px;">Portal de Cliente</h3>
      <p style="color:#ccc;font-size:13px;">Gestione su suscripción, facturas y usuarios desde el portal.</p>
      <a href="{portal_url}" style="display:inline-block;background:#e74c3c;color:#fff;padding:10px 22px;border-radius:6px;text-decoration:none;font-weight:600;font-size:14px;">
        Ir al Portal →
      </a>
    </div>

    <p style="color:#f39c12;font-size:13px;margin-top:20px;">⚠️ Por seguridad, cambie su contraseña después del primer inicio de sesión.</p>
    """

    return send_email(
        to_email=to_email,
        subject=f"🚀 Su espacio de trabajo está listo — {company_name} | SAJET",
        html_body=_base_template(content),
        text_body=(
            f"Espacio de trabajo listo — {company_name}\n"
            f"URL: {url}\n"
            f"Admin: {admin_login} / {admin_password}\n"
            f"Usuario: {user_login} / {user_password}\n"
            f"Orden: {order_number}"
        ),
        email_type="work_order_completion",
    )


def send_payment_failed_email(
    to_email: str,
    company_name: str,
    plan_name: str,
    amount: float,
    attempt_count: int = 1,
    next_retry_date: Optional[str] = None,
    update_payment_url: Optional[str] = None,
    customer_id: Optional[int] = None,
) -> dict:
    """
    Email de dunning — Notifica al cliente que su pago falló.
    Escala urgencia según número de intento.
    """
    if not update_payment_url:
        update_payment_url = f"{APP_URL}/#/billing"

    # Escalar urgencia según intento
    if attempt_count <= 1:
        urgency_color = "#f39c12"  # Amarillo
        urgency_icon = "⚠️"
        urgency_title = "Problema con su pago"
        urgency_message = "Hemos detectado un problema al procesar su pago. Por favor, actualice su método de pago para evitar interrupciones en su servicio."
    elif attempt_count == 2:
        urgency_color = "#e67e22"  # Naranja
        urgency_icon = "🔴"
        urgency_title = "Segundo intento de cobro fallido"
        urgency_message = "Este es el segundo intento fallido de cobro. Si no actualiza su método de pago pronto, su servicio podría ser suspendido."
    else:
        urgency_color = "#e74c3c"  # Rojo
        urgency_icon = "🚨"
        urgency_title = "Acción urgente requerida — Servicio en riesgo"
        urgency_message = "Se han agotado los intentos automáticos de cobro. Su servicio será suspendido en las próximas 24 horas si no actualiza su método de pago."

    retry_info = ""
    if next_retry_date:
        retry_info = f"""
        <p style="color:#aaa;font-size:13px;margin-top:12px;">
            📅 Próximo intento automático: <strong style="color:#fff;">{next_retry_date}</strong>
        </p>
        """

    content = f"""
    <div style="background:{urgency_color};border-radius:8px;padding:16px;margin-bottom:16px;">
      <h2 style="margin:0;color:#fff;font-size:18px;">{urgency_icon} {urgency_title}</h2>
    </div>

    <p style="color:#ccc;font-size:14px;">{urgency_message}</p>

    <div style="background:#1a1a2e;border-radius:8px;padding:16px;margin:16px 0;">
      <table style="width:100%;color:#ccc;font-size:14px;">
        <tr><td style="padding:6px 0;color:#aaa;">Empresa:</td>
            <td style="padding:6px 0;"><strong style="color:#fff;">{company_name}</strong></td></tr>
        <tr><td style="padding:6px 0;color:#aaa;">Plan:</td>
            <td style="padding:6px 0;"><strong style="color:#fff;">{plan_name.upper()}</strong></td></tr>
        <tr><td style="padding:6px 0;color:#aaa;">Monto:</td>
            <td style="padding:6px 0;"><strong style="color:#e74c3c;">${amount:.2f} USD</strong></td></tr>
        <tr><td style="padding:6px 0;color:#aaa;">Intento:</td>
            <td style="padding:6px 0;"><strong style="color:#fff;">#{attempt_count}</strong></td></tr>
      </table>
    </div>

    {retry_info}

    <div style="text-align:center;margin:24px 0;">
      <a href="{update_payment_url}" style="display:inline-block;background:#e74c3c;color:#fff;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:700;font-size:16px;">
        Actualizar Método de Pago →
      </a>
    </div>

    <p style="color:#888;font-size:12px;margin-top:20px;">
      Si ya actualizó su método de pago, puede ignorar este mensaje. El cobro se reintentará automáticamente.
      Si necesita ayuda, contacte a <a href="mailto:soporte@sajet.us" style="color:#e74c3c;">soporte@sajet.us</a>.
    </p>
    """

    return send_email(
        to_email=to_email,
        subject=f"{urgency_icon} {urgency_title} — {company_name} | SAJET",
        html_body=_base_template(content),
        text_body=(
            f"{urgency_title}\n\n"
            f"Empresa: {company_name}\n"
            f"Plan: {plan_name}\n"
            f"Monto: ${amount:.2f} USD\n"
            f"Intento: #{attempt_count}\n\n"
            f"Actualice su método de pago: {update_payment_url}\n"
        ),
        email_type="payment_failed_dunning",
        customer_id=customer_id,
    )


def send_subscription_cancelled_email(
    to_email: str,
    company_name: str,
    plan_name: str,
    customer_id: Optional[int] = None,
) -> dict:
    """Email de notificación de suscripción cancelada."""
    content = f"""
    <div style="background:#e74c3c;border-radius:8px;padding:16px;margin-bottom:16px;">
      <h2 style="margin:0;color:#fff;font-size:18px;">🔒 Suscripción Cancelada</h2>
    </div>

    <p style="color:#ccc;font-size:14px;">
      Su suscripción al plan <strong style="color:#fff;">{plan_name.upper()}</strong> 
      para <strong style="color:#fff;">{company_name}</strong> ha sido cancelada.
    </p>

    <p style="color:#ccc;font-size:14px;">
      Su acceso a los servicios permanecerá activo hasta el final del período de facturación actual.
      Después de eso, su espacio de trabajo será archivado.
    </p>

    <div style="text-align:center;margin:24px 0;">
      <a href="{APP_URL}/#/billing" style="display:inline-block;background:#27ae60;color:#fff;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:700;font-size:16px;">
        Reactivar Suscripción →
      </a>
    </div>

    <p style="color:#888;font-size:12px;margin-top:20px;">
      Si esto fue un error o necesita ayuda, contacte a <a href="mailto:soporte@sajet.us" style="color:#e74c3c;">soporte@sajet.us</a>.
    </p>
    """

    return send_email(
        to_email=to_email,
        subject=f"🔒 Suscripción Cancelada — {company_name} | SAJET",
        html_body=_base_template(content),
        text_body=(
            f"Suscripción Cancelada\n\n"
            f"Su plan {plan_name} para {company_name} ha sido cancelado.\n"
            f"Reactivar: {APP_URL}/#/billing\n"
        ),
        email_type="subscription_cancelled",
        customer_id=customer_id,
    )
