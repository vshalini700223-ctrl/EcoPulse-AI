import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger("ecopulse.notification")


async def dispatch_alert_notification(alert: Dict[str, Any], recipient_email: Optional[str] = None) -> Dict[str, Any]:
    """
    Dispatch an incident notification for high-severity or threshold alert.
    If SMTP credentials are provided in settings/environment variables, sends a real email.
    Otherwise, logs a simulated environmental notification event cleanly.
    """
    target_email = recipient_email or settings.ALERT_NOTIFICATION_EMAIL or "operator@ecopulse.ai"
    alert_title = alert.get("title", "Environmental Alert")
    severity = alert.get("severity", "warning").upper()
    location_name = alert.get("location_name") or alert.get("location_id", "Station")
    metric_name = alert.get("metric_name", "Telemetry")
    metric_value = alert.get("metric_value", "N/A")
    threshold_desc = alert.get("threshold_description", "Threshold exceeded")
    alert_id = alert.get("id", "N/A")
    timestamp = alert.get("created_at", "N/A")

    subject = f"[{severity}] EcoPulse AI Incident Alert: {alert_title} at {location_name}"
    
    body_text = f"""
EcoPulse AI - Environmental Alert Dispatch
=====================================================
Incident ID:     {alert_id}
Severity:        {severity}
Station:         {location_name}
Metric:          {metric_name}
Measured Value:  {metric_value}
Condition:       {threshold_desc}
Timestamp (UTC): {timestamp}
=====================================================
Please review this environmental telemetry incident in the EcoPulse AI Dashboard:
http://localhost:5173
    """.strip()

    # Check if SMTP is configured
    if settings.SMTP_HOST.strip():
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.ALERT_EMAIL_FROM
            msg["To"] = target_email

            part1 = MIMEText(body_text, "plain")
            msg.attach(part1)

            # Connect and send
            port = settings.SMTP_PORT or 587
            server = smtplib.SMTP(settings.SMTP_HOST, port, timeout=10)
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            
            server.sendmail(settings.ALERT_EMAIL_FROM, [target_email], msg.as_string())
            server.quit()

            logger.info(f"Alert email dispatched to {target_email} via SMTP ({settings.SMTP_HOST})")
            return {
                "status": "sent",
                "method": "smtp",
                "recipient": target_email,
                "subject": subject
            }
        except Exception as e:
            logger.warning(f"SMTP notification dispatch failed: {e}. Falling back to simulation log.")
            return {
                "status": "failed",
                "method": "smtp",
                "error": str(e),
                "recipient": target_email
            }
    else:
        # SMTP not configured - simulate dispatch in logs
        logger.info(
            f"[ALERT NOTIFICATION SIMULATED] To: {target_email} | Subject: {subject} | Metric: {metric_name}={metric_value}"
        )
        return {
            "status": "simulated",
            "method": "mock_log",
            "recipient": target_email,
            "subject": subject
        }
