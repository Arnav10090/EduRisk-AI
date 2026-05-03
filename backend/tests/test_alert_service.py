"""
Tests for alert notification system.

Feature: edurisk-submission-improvements
Requirements: 32.1, 32.2, 32.3, 32.4
"""
import pytest
import logging
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from backend.services.alert_service import AlertService
from backend.models.student import Student
from backend.models.prediction import Prediction


class TestHighRiskAlerts:
    """Test high-risk alert triggering."""
    
    @pytest.mark.asyncio
    async def test_high_risk_triggers_alert(self, caplog):
        """
        Risk score >= 67 should trigger alert.
        
        Requirement 32.2: Trigger alert when risk_score >= 67
        Requirement 32.3: Log alert notifications to stdout
        """
        caplog.set_level(logging.INFO)
        
        alert_service = AlertService()
        
        # Create mock student and prediction
        student = Student(
            id=uuid4(),
            name="Test Student",
            course_type="Engineering",
            institute_tier=2,
            cgpa=7.5,
            cgpa_scale=10.0,
            year_of_grad=2024,
            internship_count=1,
            internship_months=3,
            certifications=0
        )
        
        prediction = Prediction(
            id=uuid4(),
            student_id=student.id,
            risk_score=75,
            risk_level="high",
            placement_prob_3m=0.3,
            placement_prob_6m=0.5,
            placement_prob_12m=0.7,
            predicted_salary=450000,
            model_version="1.0.0",
            recommended_actions=["Improve technical skills", "Apply to more companies"]
        )
        
        # Mock database session
        mock_db = AsyncMock()
        
        # Send alert
        result = await alert_service.send_high_risk_alert(
            student=student,
            prediction=prediction,
            db=mock_db
        )
        
        # Check that alert was sent
        assert result is True
        
        # Check logs for SMS and email (Requirement 32.3)
        log_messages = [record.message for record in caplog.records]
        assert any("SMS sent" in msg and "Test Student" in msg for msg in log_messages)
        assert any("Email sent" in msg and "Test Student" in msg for msg in log_messages)
        assert any("Risk: 75" in msg for msg in log_messages)
    
    @pytest.mark.asyncio
    async def test_medium_risk_no_alert(self, caplog):
        """
        Risk score < 67 should not trigger alert.
        
        Requirement 32.2: Only trigger alert when risk_score >= 67
        """
        caplog.set_level(logging.INFO)
        
        alert_service = AlertService()
        
        # Create mock student and prediction with medium risk
        student = Student(
            id=uuid4(),
            name="Test Student",
            course_type="Engineering",
            institute_tier=2,
            cgpa=7.5,
            cgpa_scale=10.0,
            year_of_grad=2024,
            internship_count=1,
            internship_months=3,
            certifications=0
        )
        
        prediction = Prediction(
            id=uuid4(),
            student_id=student.id,
            risk_score=50,
            risk_level="medium",
            placement_prob_3m=0.5,
            placement_prob_6m=0.7,
            placement_prob_12m=0.85,
            predicted_salary=550000,
            model_version="1.0.0",
            recommended_actions=["Continue current path"]
        )
        
        # Mock database session
        mock_db = AsyncMock()
        
        # Send alert (should be skipped)
        result = await alert_service.send_high_risk_alert(
            student=student,
            prediction=prediction,
            db=mock_db
        )
        
        # Check that alert was NOT sent
        assert result is False
        
        # No SMS or email alerts should be logged
        log_messages = [record.message for record in caplog.records]
        assert not any("SMS sent" in msg for msg in log_messages)
        assert not any("Email sent" in msg for msg in log_messages)
    
    @pytest.mark.asyncio
    async def test_low_risk_no_alert(self, caplog):
        """
        Risk score < 67 (low risk) should not trigger alert.
        
        Requirement 32.2: Only trigger alert when risk_score >= 67
        """
        caplog.set_level(logging.INFO)
        
        alert_service = AlertService()
        
        # Create mock student and prediction with low risk
        student = Student(
            id=uuid4(),
            name="Test Student",
            course_type="Engineering",
            institute_tier=1,
            cgpa=9.0,
            cgpa_scale=10.0,
            year_of_grad=2024,
            internship_count=3,
            internship_months=12,
            certifications=2
        )
        
        prediction = Prediction(
            id=uuid4(),
            student_id=student.id,
            risk_score=20,
            risk_level="low",
            placement_prob_3m=0.9,
            placement_prob_6m=0.95,
            placement_prob_12m=0.98,
            predicted_salary=800000,
            model_version="1.0.0",
            recommended_actions=["Maintain current trajectory"]
        )
        
        # Mock database session
        mock_db = AsyncMock()
        
        # Send alert (should be skipped)
        result = await alert_service.send_high_risk_alert(
            student=student,
            prediction=prediction,
            db=mock_db
        )
        
        # Check that alert was NOT sent
        assert result is False
        
        # No SMS or email alerts should be logged
        log_messages = [record.message for record in caplog.records]
        assert not any("SMS sent" in msg for msg in log_messages)
        assert not any("Email sent" in msg for msg in log_messages)
    
    @pytest.mark.asyncio
    async def test_alert_disabled_no_notification(self, caplog, monkeypatch):
        """
        When ALERT_ENABLED=False, no alerts should be sent.
        
        Requirement 32.3.4: Skip alerts if ALERT_ENABLED=False
        """
        caplog.set_level(logging.INFO)
        
        # Set ALERT_ENABLED to false
        monkeypatch.setenv("ALERT_ENABLED", "false")
        
        # Create new alert service with disabled alerts
        alert_service = AlertService()
        
        # Create mock student and prediction with high risk
        student = Student(
            id=uuid4(),
            name="Test Student",
            course_type="Engineering",
            institute_tier=2,
            cgpa=7.5,
            cgpa_scale=10.0,
            year_of_grad=2024,
            internship_count=1,
            internship_months=3,
            certifications=0
        )
        
        prediction = Prediction(
            id=uuid4(),
            student_id=student.id,
            risk_score=75,
            risk_level="high",
            placement_prob_3m=0.3,
            placement_prob_6m=0.5,
            placement_prob_12m=0.7,
            predicted_salary=450000,
            model_version="1.0.0",
            recommended_actions=["Improve technical skills"]
        )
        
        # Mock database session
        mock_db = AsyncMock()
        
        # Send alert (should be skipped because alerts are disabled)
        result = await alert_service.send_high_risk_alert(
            student=student,
            prediction=prediction,
            db=mock_db
        )
        
        # Check that alert was NOT sent
        assert result is False
        
        # Check that "Alerts disabled" message is logged
        log_messages = [record.message for record in caplog.records]
        assert any("Alerts disabled" in msg for msg in log_messages)
        
        # No SMS or email alerts should be sent
        assert not any("SMS sent" in msg for msg in log_messages)
        assert not any("Email sent" in msg for msg in log_messages)


class TestAlertLogging:
    """Test alert audit logging."""
    
    @pytest.mark.asyncio
    async def test_alert_logged_to_audit_trail(self):
        """
        Alert should be logged to audit_logs table.
        
        Requirement 32.4: Log alert notifications to audit_logs table
        """
        alert_service = AlertService()
        
        # Create mock student and prediction
        student = Student(
            id=uuid4(),
            name="Test Student",
            course_type="Engineering",
            institute_tier=2,
            cgpa=7.5,
            cgpa_scale=10.0,
            year_of_grad=2024,
            internship_count=1,
            internship_months=3,
            certifications=0
        )
        
        prediction = Prediction(
            id=uuid4(),
            student_id=student.id,
            risk_score=75,
            risk_level="high",
            placement_prob_3m=0.3,
            placement_prob_6m=0.5,
            placement_prob_12m=0.7,
            predicted_salary=450000,
            model_version="1.0.0",
            recommended_actions=["Improve technical skills"]
        )
        
        # Mock database session
        mock_db = AsyncMock()
        
        # Send alert
        await alert_service.send_high_risk_alert(
            student=student,
            prediction=prediction,
            db=mock_db,
            performed_by="test_user"
        )
        
        # Verify that database session was used (audit log was created)
        # The AuditLogger.log_alert_sent should have been called
        # We can't directly verify the audit log without a real database,
        # but we can verify the db session was used
        assert mock_db.method_calls  # Database methods were called


class TestAlertFormatting:
    """Test alert message formatting."""
    
    @pytest.mark.asyncio
    async def test_sms_format_includes_required_fields(self, caplog):
        """
        SMS alert should include phone, student name, and risk score.
        
        Requirement 32.3: Log format "ALERT: SMS sent to [PHONE] for student [NAME] (Risk: [SCORE])"
        """
        caplog.set_level(logging.INFO)
        
        alert_service = AlertService()
        
        # Send mock SMS
        await alert_service.mock_send_sms(
            to_phone="+1-555-0101",
            student_name="John Doe",
            risk_score=85,
            recommended_actions=["Action 1", "Action 2"]
        )
        
        # Check log format
        log_messages = [record.message for record in caplog.records]
        sms_logs = [msg for msg in log_messages if "SMS sent" in msg]
        
        assert len(sms_logs) > 0
        sms_log = sms_logs[0]
        
        # Verify required fields are present
        assert "+1-555-0101" in sms_log
        assert "John Doe" in sms_log
        assert "85" in sms_log
    
    @pytest.mark.asyncio
    async def test_email_format_includes_required_fields(self, caplog):
        """
        Email alert should include email address, student name, and risk score.
        
        Requirement 32.3: Log format "ALERT: Email sent to [ADDRESS] for student [NAME] (Risk: [SCORE])"
        """
        caplog.set_level(logging.INFO)
        
        alert_service = AlertService()
        
        # Send mock email
        await alert_service.mock_send_email(
            to_email="test@edurisk.ai",
            student_name="Jane Smith",
            risk_score=72,
            risk_level="high",
            recommended_actions=["Action 1", "Action 2", "Action 3"]
        )
        
        # Check log format
        log_messages = [record.message for record in caplog.records]
        email_logs = [msg for msg in log_messages if "Email sent" in msg]
        
        assert len(email_logs) > 0
        email_log = email_logs[0]
        
        # Verify required fields are present
        assert "test@edurisk.ai" in email_log
        assert "Jane Smith" in email_log
        assert "72" in email_log


class TestAlertConfiguration:
    """Test alert configuration from environment variables."""
    
    def test_alert_service_reads_env_config(self, monkeypatch):
        """
        AlertService should read configuration from environment variables.
        
        Requirements:
            - 32.3.1: Read ALERT_ENABLED from environment
            - 32.3.2: Read ALERT_PHONE_NUMBER from environment
            - 32.3.3: Read ALERT_EMAIL from environment
        """
        # Set environment variables
        monkeypatch.setenv("ALERT_ENABLED", "true")
        monkeypatch.setenv("ALERT_PHONE_NUMBER", "+1-555-9999")
        monkeypatch.setenv("ALERT_EMAIL", "custom@example.com")
        
        # Create alert service
        alert_service = AlertService()
        
        # Verify configuration was read
        assert alert_service.alert_enabled is True
        assert alert_service.alert_phone == "+1-555-9999"
        assert alert_service.alert_email == "custom@example.com"
    
    def test_alert_service_uses_defaults(self):
        """
        AlertService should use default values when env vars not set.
        
        Requirement 32.5: Include placeholder phone numbers for demo
        """
        # Create alert service without setting env vars
        alert_service = AlertService()
        
        # Verify defaults are used
        assert alert_service.alert_enabled is True  # Default is true
        assert alert_service.alert_phone in alert_service.DEMO_PHONE_NUMBERS.values()
        assert alert_service.alert_email in alert_service.DEMO_EMAIL_ADDRESSES.values()
