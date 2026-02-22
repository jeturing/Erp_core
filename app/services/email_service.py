"""
Email Transactional Service — SMTP (ipzmarketing/mailrelay)
Envía correos transaccionales: credenciales, facturas, notificaciones.
"""
import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)

# SMTP Configuration — ipzmarketing mailrelay
SMTP_HOST = os.getenv("SMTP_HOST", "smtp1.s.ipzmarketing.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "xjbmlqganpkd")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "U5VBlQnjiZpMwgLr")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "no-reply@sajet.us")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "SAJET Platform")
SMTP_ENCRYPTION = os.getenv("SMTP_ENCRYPTION", "SSL/TLS")  # SSL/TLS o STARTTLS

APP_URL = os.getenv("APP_URL", "https://sajet.us")


def _get_smtp_connection():
    """Crea conexión SMTP con SSL/TLS"""
    if SMTP_ENCRYPTION == "STARTTLS":
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
        server.ehlo()
        server.starttls()
        server.ehlo()
    else:
        # SSL/TLS por defecto (puerto 465)
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30)
    
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
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        if reply_to:
            msg["Reply-To"] = reply_to

        # Texto plano como fallback
        if text_body:
            msg.attach(MIMEText(text_body, "plain", "utf-8"))

        # HTML principal
        msg.attach(MIMEText(html_body, "html", "utf-8"))

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
