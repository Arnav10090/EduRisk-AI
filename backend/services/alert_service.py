"""
Mock alert notification system for EduRisk AI.

Demonstrates how the system would notify loan officers of high-risk students.
In production, integrate with Twilio (SMS) and SendGrid (email).

Feature: edurisk-submission-improvements
Requirements: 32.1, 32.2, 32.3, 32.4, 32.5, 32.6, 32.7, 32.8
"""
import logging
import os
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.student import Student
from backend.models.prediction import Prediction
from backend.services.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


class AlertService:
    """
    Service for sending alert notifications for high-risk students.
    
    This service provides mock SMS and email notification capabilities
    for demonstration purposes. In production, integrate with Twilio (SMS)
    and SendGrid (email) by replacing the mock functions.
    
    Requirements:
        - 32.1: Provide AlertService class in backend/services/alert_service.py
        - 32.2: Trigger alerts when risk_score >= 67
        - 32.3: Log alert notifications to stdout
        - 32.4: Log alert notifications to audit_logs table
        - 32.5: Include placeholder phone numbers for demo
        - 32.6: Provide mock_send_sms() with Twilio-compatible signature
        - 32.7: Provide mock_send_email() with SendGrid-compatible signature
        - 32.8: Include comments for real integration points
    """
    
    # Mock phone numbers for demo (Requirement 32.5)
    DEMO_PHONE_NUMBERS = {
        "loan_officer_1": "+1-555-0101",
        "loan_officer_2": "+1-555-0102",
        "manager": "+1-555-0199"
    }
    
    # Mock email addresses for demo
    DEMO_EMAIL_ADDRESSES = {
        "loan_officer_1": "loan.officer1@edurisk.ai",
        "loan_officer_2": "loan.officer2@edurisk.ai",
        "manager": "manager@edurisk.ai"
    }
    
    def __init__(self):
        """Initialize AlertService with configuration from environment."""
        # Read alert configuration from environment (Requirement 32.3)
        self.alert_enabled = os.getenv("ALERT_ENABLED", "true").lower() == "true"
        self.alert_phone = os.getenv("ALERT_PHONE_NUMBER", self.DEMO_PHONE_NUMBERS["loan_officer_1"])
        self.alert_email = os.getenv("ALERT_EMAIL", self.DEMO_EMAIL_ADDRESSES["loan_officer_1"])
        
        logger.info(
            f"AlertService initialized - Enabled: {self.alert_enabled}, "
            f"Phone: {self.alert_phone}, Email: {self.alert_email}"
        )
    
    async def send_high_risk_alert(
        self,
        student: Student,
        prediction: Prediction,
        db: AsyncSession,
        performed_by: str = "system"
    ) -> bool:
        """
        Send alert notification for high-risk student.
        
        Triggers when risk_score >= 67. Sends both SMS and email notifications
        and logs the alert to the audit trail.
        
        Args:
            student: Student ORM object with student information
            prediction: Prediction ORM object with risk assessment
            db: Database session for audit logging
            performed_by: User or system identifier (default: "system")
            
        Returns:
            True if alert was sent, False if skipped (not high-risk or disabled)
            
        Requirements:
            - 32.2: Trigger alert when risk_score >= 67
            - 32.3: Log alert notifications to stdout
            - 32.4: Log alert notifications to audit_logs table
        """
        # Check if alerts are enabled (Requirement 32.3.4)
        if not self.alert_enabled:
            logger.info(f"Alerts disabled - skipping alert for student {student.name}")
            return False
        
        # Only alert for high-risk students (Requirement 32.2)
        if prediction.risk_score < 67:
            logger.debug(
                f"Student {student.name} risk score {prediction.risk_score} < 67 - "
                f"no alert triggered"
            )
            return False
        
        logger.info(
            f"High-risk student detected: {student.name} "
            f"(Risk Score: {prediction.risk_score}) - triggering alerts"
        )
        
        # Send mock SMS notification (Requirement 32.6)
        await self.mock_send_sms(
            to_phone=self.alert_phone,
            student_name=student.name,
            risk_score=prediction.risk_score,
            recommended_actions=prediction.next_best_actions or []
        )
        
        # Send mock email notification (Requirement 32.7)
        await self.mock_send_email(
            to_email=self.alert_email,
            student_name=student.name,
            risk_score=prediction.risk_score,
            risk_level=prediction.risk_level,
            recommended_actions=prediction.next_best_actions or []
        )
        
        # Log alert to audit trail (Requirement 32.4)
        await AuditLogger.log_alert_sent(
            db=db,
            student_id=student.id,
            prediction_id=prediction.id,
            alert_type="high_risk",
            risk_score=prediction.risk_score,
            performed_by=performed_by,
            metadata={
                "notification_channels": ["sms", "email"],
                "phone_number": self.alert_phone,
                "email_address": self.alert_email,
                "risk_level": prediction.risk_level
            }
        )
        
        logger.info(
            f"Alert sent and logged for student {student.name} "
            f"(Prediction ID: {prediction.id})"
        )
        
        return True
    
    async def mock_send_sms(
        self,
        to_phone: str,
        student_name: str,
        risk_score: int,
        recommended_actions: list[str]
    ):
        """
        Mock SMS notification function with Twilio-compatible signature.
        
        In production, replace with Twilio integration:
        ```python
        from twilio.rest import Client
        
        # Initialize Twilio client (Requirement 32.8)
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        from_phone = os.getenv('TWILIO_PHONE_NUMBER')
        
        client = Client(account_sid, auth_token)
        
        # Compose message
        message_body = (
            f"ALERT: High-risk student {student_name} (Risk: {risk_score}). "
            f"Actions: {', '.join(recommended_actions[:2])}"
        )
        
        # Send SMS via Twilio API
        message = client.messages.create(
            body=message_body,
            from_=from_phone,
            to=to_phone
        )
        
        logger.info(f"SMS sent via Twilio - SID: {message.sid}")
        ```
        
        Args:
            to_phone: Recipient phone number (E.164 format)
            student_name: Name of the high-risk student
            risk_score: Computed risk score (0-100)
            recommended_actions: List of recommended intervention actions
            
        Requirements:
            - 32.3: Log alert to stdout in specified format
            - 32.6: Provide Twilio-compatible function signature
            - 32.8: Include comments for real Twilio integration
        """
        # Format recommended actions for SMS (limit to 2 for brevity)
        actions_text = ", ".join(recommended_actions[:2]) if recommended_actions else "Review profile"
        
        # Log mock SMS (Requirement 32.3)
        log_message = (
            f"ALERT: SMS sent to {to_phone} for student {student_name} "
            f"(Risk: {risk_score})"
        )
        logger.info(f"📱 {log_message}")
        
        # Log detailed message content
        logger.debug(
            f"SMS Content: High-risk student {student_name} detected. "
            f"Risk Score: {risk_score}. Recommended Actions: {actions_text}"
        )
        
        # In production, this would make actual Twilio API call
        # See docstring above for integration code (Requirement 32.8)
    
    async def mock_send_email(
        self,
        to_email: str,
        student_name: str,
        risk_score: int,
        risk_level: str,
        recommended_actions: list[str]
    ):
        """
        Mock email notification function with SendGrid-compatible signature.
        
        In production, replace with SendGrid integration:
        ```python
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        # Initialize SendGrid client (Requirement 32.8)
        api_key = os.getenv('SENDGRID_API_KEY')
        from_email = os.getenv('SENDGRID_FROM_EMAIL', 'alerts@edurisk.ai')
        
        # Compose HTML email
        html_content = f'''
        <html>
        <body>
            <h2>High Risk Alert: {student_name}</h2>
            <p><strong>Risk Level:</strong> {risk_level.upper()}</p>
            <p><strong>Risk Score:</strong> {risk_score}/100</p>
            <h3>Recommended Actions:</h3>
            <ul>
                {''.join(f'<li>{action}</li>' for action in recommended_actions)}
            </ul>
            <p>Please review this student's profile and take appropriate action.</p>
        </body>
        </html>
        '''
        
        # Create email message
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=f'High Risk Alert: {student_name}',
            html_content=html_content
        )
        
        # Send email via SendGrid API
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        logger.info(f"Email sent via SendGrid - Status: {response.status_code}")
        ```
        
        Args:
            to_email: Recipient email address
            student_name: Name of the high-risk student
            risk_score: Computed risk score (0-100)
            risk_level: Risk level classification (low/medium/high)
            recommended_actions: List of recommended intervention actions
            
        Requirements:
            - 32.3: Log alert to stdout in specified format
            - 32.7: Provide SendGrid-compatible function signature
            - 32.8: Include comments for real SendGrid integration
        """
        # Format recommended actions for email
        actions_text = "\n  - ".join(recommended_actions) if recommended_actions else "Review student profile"
        
        # Log mock email (Requirement 32.3)
        log_message = (
            f"ALERT: Email sent to {to_email} for student {student_name} "
            f"(Risk: {risk_score})"
        )
        logger.info(f"📧 {log_message}")
        
        # Log detailed email content
        logger.debug(
            f"Email Content:\n"
            f"  Subject: High Risk Alert - {student_name}\n"
            f"  Risk Level: {risk_level.upper()}\n"
            f"  Risk Score: {risk_score}/100\n"
            f"  Recommended Actions:\n  - {actions_text}"
        )
        
        # In production, this would make actual SendGrid API call
        # See docstring above for integration code (Requirement 32.8)
