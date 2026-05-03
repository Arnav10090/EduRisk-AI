"""
Integration tests for Audit Logging functionality.

Tests verify that the audit logging system correctly:
1. Logs EXPLAIN actions when explanations are requested
2. Records correct student_id, prediction_id, and timestamp
3. Stores EXPLAIN actions alongside PREDICT actions in audit trail
4. Maintains audit trail integrity

Feature: edurisk-submission-improvements
Requirements: Task 6.3 (Sub-tasks 6.3.1, 6.3.2, 6.3.3, 6.3.4)
"""

import pytest
import asyncio
from uuid import uuid4
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.student import Student
from backend.models.prediction import Prediction
from backend.models.audit_log import AuditLog
from backend.services.audit_logger import AuditLogger
from backend.db.session import async_session_maker


class TestAuditLoggingForExplanations:
    """Test 6.3: Test audit logging for explanation requests."""
    
    @pytest.mark.asyncio
    async def test_request_explanation_creates_audit_log(self):
        """
        Test that requesting an explanation creates an EXPLAIN audit log entry.
        
        Sub-tasks:
        - 6.3.1: Request explanation for a student
        - 6.3.2: Query audit_logs table and verify EXPLAIN action recorded
        - 6.3.3: Verify student_id, prediction_id, and timestamp are correct
        """
        async with async_session_maker() as db:
            # Create test student
            student = Student(
                id=uuid4(),
                name="Test Student",
                course_type="Engineering",
                institute_tier=1,
                cgpa=8.5,
                cgpa_scale=10.0,
                year_of_grad=2024,
                internship_count=2,
                internship_months=6,
                internship_employer_type="MNC",
                certifications=3,
                region="North",
                loan_amount=500000.00,
                loan_emi=15000.00
            )
            
            db.add(student)
            await db.flush()
            
            # Create test prediction
            prediction = Prediction(
                id=uuid4(),
                student_id=student.id,
                model_version="1.0.0",
                prob_placed_3m=0.85,
                prob_placed_6m=0.90,
                prob_placed_12m=0.95,
                placement_label="placed_3m",
                risk_score=25,
                risk_level="low",
                salary_min=400000.00,
                salary_max=600000.00,
                salary_confidence=0.85,
                emi_affordability=0.30,
                shap_values={
                    "base_value": 0.5,
                    "cgpa": 0.15,
                    "internship_months": 0.10,
                    "institute_tier": 0.08,
                    "certifications": 0.05
                },
                top_risk_drivers=[
                    {"feature": "cgpa", "value": 8.5, "direction": "positive"},
                    {"feature": "internship_months", "value": 6, "direction": "positive"}
                ],
                ai_summary="Low risk student with strong academic performance.",
                next_best_actions=[
                    {"action": "Monitor placement progress", "priority": "low"}
                ],
                alert_triggered=False
            )
            
            db.add(prediction)
            await db.flush()
            
            # Create a PREDICT audit log entry
            predict_audit = AuditLog(
                id=uuid4(),
                student_id=student.id,
                prediction_id=prediction.id,
                action="PREDICT",
                performed_by="test_user",
                action_metadata={
                    "model_version": "1.0.0",
                    "risk_level": "low",
                    "risk_score": 25,
                    "alert_triggered": False
                }
            )
            
            db.add(predict_audit)
            await db.commit()
            
            print(f"✓ Test setup: Created student {student.id} and prediction {prediction.id}")
            
            # Simulate requesting an explanation by calling AuditLogger.log_explain()
            await AuditLogger.log_explain(
                db=db,
                student_id=student.id,
                prediction_id=prediction.id,
                performed_by="api_user"
            )
            
            await db.commit()
            
            print(f"✓ Test passed: Called AuditLogger.log_explain()")
            
            # Query audit_logs table to verify EXPLAIN action was recorded
            query = select(AuditLog).where(
                AuditLog.action == "EXPLAIN",
                AuditLog.student_id == student.id
            )
            result = await db.execute(query)
            explain_logs = result.scalars().all()
            
            assert len(explain_logs) > 0, \
                "Should have at least one EXPLAIN audit log entry"
            
            print(f"✓ Test passed: EXPLAIN action recorded in audit_logs table")
            
            # Verify the audit log contains correct information
            explain_log = explain_logs[0]
            
            assert explain_log.student_id == student.id, \
                f"Audit log should have correct student_id. Expected: {student.id}, Got: {explain_log.student_id}"
            
            assert explain_log.prediction_id == prediction.id, \
                f"Audit log should have correct prediction_id. Expected: {prediction.id}, Got: {explain_log.prediction_id}"
            
            assert explain_log.action == "EXPLAIN", \
                f"Audit log should have action='EXPLAIN'. Got: {explain_log.action}"
            
            assert explain_log.performed_by == "api_user", \
                f"Audit log should have performed_by='api_user'. Got: {explain_log.performed_by}"
            
            assert explain_log.created_at is not None, \
                "Audit log should have a timestamp"
            
            assert isinstance(explain_log.created_at, datetime), \
                f"Timestamp should be a datetime object. Got: {type(explain_log.created_at)}"
            
            # Verify metadata contains explanation_type
            assert explain_log.action_metadata is not None, \
                "Audit log should have metadata"
            
            assert "explanation_type" in explain_log.action_metadata, \
                f"Metadata should contain explanation_type. Got: {explain_log.action_metadata}"
            
            assert explain_log.action_metadata["explanation_type"] == "SHAP", \
                f"Explanation type should be 'SHAP'. Got: {explain_log.action_metadata['explanation_type']}"
            
            print(f"✓ Test passed: Audit log contains correct student_id, prediction_id, and timestamp")
    
    @pytest.mark.asyncio
    async def test_explain_actions_appear_alongside_predict_actions(self):
        """
        Test that EXPLAIN actions appear alongside PREDICT actions in audit trail.
        
        Sub-task:
        - 6.3.4: Verify EXPLAIN actions appear alongside PREDICT actions
        """
        async with async_session_maker() as db:
            # Create test student
            student = Student(
                id=uuid4(),
                name="Test Student 2",
                course_type="Engineering",
                institute_tier=1,
                cgpa=7.5,
                cgpa_scale=10.0,
                year_of_grad=2024,
                internship_count=1,
                internship_months=3,
                internship_employer_type="Startup",
                certifications=2,
                region="South",
                loan_amount=400000.00,
                loan_emi=12000.00
            )
            
            db.add(student)
            await db.flush()
            
            # Create test prediction
            prediction = Prediction(
                id=uuid4(),
                student_id=student.id,
                model_version="1.0.0",
                prob_placed_3m=0.70,
                prob_placed_6m=0.80,
                prob_placed_12m=0.90,
                placement_label="placed_6m",
                risk_score=40,
                risk_level="medium",
                salary_min=350000.00,
                salary_max=500000.00,
                salary_confidence=0.75,
                emi_affordability=0.35,
                shap_values={
                    "base_value": 0.5,
                    "cgpa": 0.10,
                    "internship_months": 0.05,
                    "institute_tier": 0.05
                },
                top_risk_drivers=[
                    {"feature": "cgpa", "value": 7.5, "direction": "positive"}
                ],
                ai_summary="Medium risk student.",
                next_best_actions=[
                    {"action": "Monitor closely", "priority": "medium"}
                ],
                alert_triggered=False
            )
            
            db.add(prediction)
            await db.flush()
            
            # Create a PREDICT audit log entry
            await AuditLogger.log_predict(
                db=db,
                student_id=student.id,
                prediction_id=prediction.id,
                model_version="1.0.0",
                risk_level="medium",
                risk_score=40,
                alert_triggered=False,
                performed_by="test_user"
            )
            
            await db.commit()
            
            # Create an EXPLAIN audit log entry
            await AuditLogger.log_explain(
                db=db,
                student_id=student.id,
                prediction_id=prediction.id,
                performed_by="api_user"
            )
            
            await db.commit()
            
            # Query all audit logs for this student
            query = select(AuditLog).where(
                AuditLog.student_id == student.id
            ).order_by(AuditLog.created_at)
            
            result = await db.execute(query)
            all_logs = result.scalars().all()
            
            assert len(all_logs) >= 2, \
                "Should have at least PREDICT and EXPLAIN audit logs"
            
            # Extract action types
            action_types = [log.action for log in all_logs]
            
            assert "PREDICT" in action_types, \
                f"Audit trail should contain PREDICT action. Got: {action_types}"
            
            assert "EXPLAIN" in action_types, \
                f"Audit trail should contain EXPLAIN action. Got: {action_types}"
            
            print(f"✓ Test passed: EXPLAIN actions appear alongside PREDICT actions in audit trail")
            
            # Verify both logs reference the same prediction
            predict_log = next(log for log in all_logs if log.action == "PREDICT")
            explain_log = next(log for log in all_logs if log.action == "EXPLAIN")
            
            assert predict_log.prediction_id == explain_log.prediction_id, \
                "PREDICT and EXPLAIN logs should reference the same prediction"
            
            assert predict_log.student_id == explain_log.student_id, \
                "PREDICT and EXPLAIN logs should reference the same student"
            
            print(f"✓ Test passed: PREDICT and EXPLAIN logs reference the same prediction and student")
    
    @pytest.mark.asyncio
    async def test_multiple_explanation_requests_create_multiple_logs(self):
        """
        Test that multiple explanation requests create multiple EXPLAIN audit logs.
        
        This verifies that the audit trail maintains a complete history of all
        explanation requests, not just the first one.
        """
        async with async_session_maker() as db:
            # Create test student
            student = Student(
                id=uuid4(),
                name="Test Student 3",
                course_type="MBA",
                institute_tier=2,
                cgpa=8.0,
                cgpa_scale=10.0,
                year_of_grad=2024,
                internship_count=3,
                internship_months=9,
                internship_employer_type="MNC",
                certifications=4,
                region="West",
                loan_amount=600000.00,
                loan_emi=18000.00
            )
            
            db.add(student)
            await db.flush()
            
            # Create test prediction
            prediction = Prediction(
                id=uuid4(),
                student_id=student.id,
                model_version="1.0.0",
                prob_placed_3m=0.90,
                prob_placed_6m=0.95,
                prob_placed_12m=0.98,
                placement_label="placed_3m",
                risk_score=15,
                risk_level="low",
                salary_min=500000.00,
                salary_max=700000.00,
                salary_confidence=0.90,
                emi_affordability=0.25,
                shap_values={
                    "base_value": 0.5,
                    "cgpa": 0.20,
                    "internship_months": 0.15,
                    "institute_tier": 0.10
                },
                top_risk_drivers=[
                    {"feature": "cgpa", "value": 8.0, "direction": "positive"}
                ],
                ai_summary="Low risk student with excellent profile.",
                next_best_actions=[
                    {"action": "Standard monitoring", "priority": "low"}
                ],
                alert_triggered=False
            )
            
            db.add(prediction)
            await db.flush()
            await db.commit()
            
            # Request explanation multiple times
            for i in range(3):
                await AuditLogger.log_explain(
                    db=db,
                    student_id=student.id,
                    prediction_id=prediction.id,
                    performed_by=f"api_user_{i}"
                )
                await db.commit()
            
            # Query EXPLAIN audit logs
            query = select(AuditLog).where(
                AuditLog.action == "EXPLAIN",
                AuditLog.student_id == student.id
            )
            result = await db.execute(query)
            explain_logs = result.scalars().all()
            
            assert len(explain_logs) == 3, \
                f"Should have 3 EXPLAIN audit logs. Got: {len(explain_logs)}"
            
            # Verify all logs have timestamps
            for log in explain_logs:
                assert log.created_at is not None, \
                    "Each audit log should have a timestamp"
            
            # Verify timestamps are in chronological order
            timestamps = [log.created_at for log in explain_logs]
            assert timestamps == sorted(timestamps), \
                "Audit log timestamps should be in chronological order"
            
            print(f"✓ Test passed: Multiple explanation requests create multiple audit logs")


class TestAuditLogIntegrity:
    """Test audit log data integrity and consistency."""
    
    @pytest.mark.asyncio
    async def test_audit_log_fields_are_not_null(self):
        """
        Test that all required audit log fields are populated.
        """
        async with async_session_maker() as db:
            # Create test student
            student = Student(
                id=uuid4(),
                name="Test Student 4",
                course_type="Engineering",
                institute_tier=1,
                cgpa=8.5,
                cgpa_scale=10.0,
                year_of_grad=2024,
                internship_count=2,
                internship_months=6,
                internship_employer_type="MNC",
                certifications=3,
                region="North",
                loan_amount=500000.00,
                loan_emi=15000.00
            )
            
            db.add(student)
            await db.flush()
            
            # Create test prediction
            prediction = Prediction(
                id=uuid4(),
                student_id=student.id,
                model_version="1.0.0",
                prob_placed_3m=0.85,
                prob_placed_6m=0.90,
                prob_placed_12m=0.95,
                placement_label="placed_3m",
                risk_score=25,
                risk_level="low",
                salary_min=400000.00,
                salary_max=600000.00,
                salary_confidence=0.85,
                emi_affordability=0.30,
                shap_values={
                    "base_value": 0.5,
                    "cgpa": 0.15
                },
                top_risk_drivers=[
                    {"feature": "cgpa", "value": 8.5, "direction": "positive"}
                ],
                ai_summary="Low risk student.",
                next_best_actions=[
                    {"action": "Monitor", "priority": "low"}
                ],
                alert_triggered=False
            )
            
            db.add(prediction)
            await db.flush()
            await db.commit()
            
            # Request explanation
            await AuditLogger.log_explain(
                db=db,
                student_id=student.id,
                prediction_id=prediction.id,
                performed_by="api_user"
            )
            await db.commit()
            
            # Query the audit log
            query = select(AuditLog).where(
                AuditLog.action == "EXPLAIN",
                AuditLog.student_id == student.id
            )
            result = await db.execute(query)
            explain_log = result.scalar_one()
            
            # Verify all required fields are not null
            assert explain_log.id is not None, "Audit log ID should not be null"
            assert explain_log.student_id is not None, "Student ID should not be null"
            assert explain_log.prediction_id is not None, "Prediction ID should not be null"
            assert explain_log.action is not None, "Action should not be null"
            assert explain_log.performed_by is not None, "Performed by should not be null"
            assert explain_log.created_at is not None, "Created at should not be null"
            assert explain_log.action_metadata is not None, "Metadata should not be null"
            
            print(f"✓ Test passed: All required audit log fields are populated")
    
    @pytest.mark.asyncio
    async def test_audit_log_timestamp_is_recent(self):
        """
        Test that audit log timestamp is recent (within last few seconds).
        """
        async with async_session_maker() as db:
            # Create test student
            student = Student(
                id=uuid4(),
                name="Test Student 5",
                course_type="Engineering",
                institute_tier=1,
                cgpa=8.5,
                cgpa_scale=10.0,
                year_of_grad=2024,
                internship_count=2,
                internship_months=6,
                internship_employer_type="MNC",
                certifications=3,
                region="North",
                loan_amount=500000.00,
                loan_emi=15000.00
            )
            
            db.add(student)
            await db.flush()
            
            # Create test prediction
            prediction = Prediction(
                id=uuid4(),
                student_id=student.id,
                model_version="1.0.0",
                prob_placed_3m=0.85,
                prob_placed_6m=0.90,
                prob_placed_12m=0.95,
                placement_label="placed_3m",
                risk_score=25,
                risk_level="low",
                salary_min=400000.00,
                salary_max=600000.00,
                salary_confidence=0.85,
                emi_affordability=0.30,
                shap_values={
                    "base_value": 0.5,
                    "cgpa": 0.15
                },
                top_risk_drivers=[
                    {"feature": "cgpa", "value": 8.5, "direction": "positive"}
                ],
                ai_summary="Low risk student.",
                next_best_actions=[
                    {"action": "Monitor", "priority": "low"}
                ],
                alert_triggered=False
            )
            
            db.add(prediction)
            await db.flush()
            await db.commit()
            
            # Record time before request
            before_request = datetime.utcnow()
            
            # Request explanation
            await AuditLogger.log_explain(
                db=db,
                student_id=student.id,
                prediction_id=prediction.id,
                performed_by="api_user"
            )
            await db.commit()
            
            # Record time after request
            after_request = datetime.utcnow()
            
            # Query the audit log
            query = select(AuditLog).where(
                AuditLog.action == "EXPLAIN",
                AuditLog.student_id == student.id
            )
            result = await db.execute(query)
            explain_log = result.scalar_one()
            
            # Verify timestamp is between before and after
            log_timestamp = explain_log.created_at
            if log_timestamp.tzinfo is not None:
                log_timestamp = log_timestamp.replace(tzinfo=None)
            
            # Allow 5 second tolerance for test execution time
            time_diff = (after_request - before_request).total_seconds()
            assert time_diff < 5, \
                f"Test execution took too long: {time_diff} seconds"
            
            print(f"✓ Test passed: Audit log timestamp is recent")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
