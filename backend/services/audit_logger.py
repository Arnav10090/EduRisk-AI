"""
Audit Logger Service for EduRisk AI

This module provides audit logging functionality for compliance tracking.
All predictions, explanations, and alerts are logged to maintain an
append-only audit trail for RBI regulatory compliance.

Feature: edurisk-ai-placement-intelligence
Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7
"""

from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.audit_log import AuditLog


class AuditLogger:
    """
    Service for creating audit log entries for compliance tracking.
    
    This service maintains an append-only audit trail of all system actions
    including predictions, explanations, and alerts. Records are never deleted
    to ensure compliance with RBI regulatory requirements.
    
    Supported action types:
        - PREDICT: When a placement prediction is generated
        - EXPLAIN: When a SHAP explanation is retrieved
        - ALERT_SENT: When a high-risk alert is triggered
    
    Requirements:
        - 14.1: Create audit log record with action "PREDICT"
        - 14.2: Create audit log record with action "EXPLAIN"
        - 14.3: Create audit log record with action "ALERT_SENT"
        - 14.4: Store student_id, prediction_id, action, performed_by, metadata
        - 14.5: Include model_version in metadata for PREDICT actions
        - 14.6: Record timestamp automatically using database default NOW()
        - 14.7: Never delete audit log records (append-only table)
    """
    
    @staticmethod
    async def log_action(
        db: AsyncSession,
        action: str,
        student_id: Optional[UUID] = None,
        prediction_id: Optional[UUID] = None,
        performed_by: Optional[str] = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Create an audit log entry for a system action.
        
        This method creates an append-only audit log record for compliance
        tracking. All actions are logged with timestamp, action type, and
        optional metadata.
        
        Args:
            db: Async database session
            action: Action type (PREDICT, EXPLAIN, ALERT_SENT)
            student_id: Optional UUID of the student record
            prediction_id: Optional UUID of the prediction record
            performed_by: User or system identifier (default: "system")
            metadata: Optional dictionary with additional action metadata
            
        Returns:
            Created AuditLog ORM object
            
        Raises:
            ValueError: If action type is not supported
            
        Requirements:
            - 14.1: Log PREDICT actions when predictions are generated
            - 14.2: Log EXPLAIN actions when explanations are retrieved
            - 14.3: Log ALERT_SENT actions when high-risk alerts are triggered
            - 14.4: Store all required fields in audit log
            - 14.5: Include model_version in metadata for PREDICT actions
            - 14.6: Timestamp recorded automatically by database
            - 14.7: Records are never deleted (append-only)
            
        Example:
            >>> # Log a prediction action
            >>> await AuditLogger.log_action(
            ...     db=db,
            ...     action="PREDICT",
            ...     student_id=student_id,
            ...     prediction_id=prediction_id,
            ...     performed_by="loan_officer_123",
            ...     metadata={
            ...         "model_version": "1.0.0",
            ...         "risk_level": "high",
            ...         "risk_score": 75,
            ...         "alert_triggered": True
            ...     }
            ... )
            
            >>> # Log an explanation retrieval
            >>> await AuditLogger.log_action(
            ...     db=db,
            ...     action="EXPLAIN",
            ...     student_id=student_id,
            ...     prediction_id=prediction_id,
            ...     performed_by="loan_officer_123",
            ...     metadata={"explanation_type": "shap_waterfall"}
            ... )
            
            >>> # Log a high-risk alert
            >>> await AuditLogger.log_action(
            ...     db=db,
            ...     action="ALERT_SENT",
            ...     student_id=student_id,
            ...     prediction_id=prediction_id,
            ...     performed_by="system",
            ...     metadata={
            ...         "alert_type": "high_risk",
            ...         "risk_score": 85,
            ...         "emi_affordability": 0.65
            ...     }
            ... )
        """
        # Validate action type (Requirements 14.1, 14.2, 14.3)
        valid_actions = ["PREDICT", "EXPLAIN", "ALERT_SENT"]
        if action not in valid_actions:
            raise ValueError(
                f"Invalid action type '{action}'. "
                f"Must be one of: {', '.join(valid_actions)}"
            )
        
        # Validate metadata for PREDICT actions (Requirement 14.5)
        if action == "PREDICT" and metadata:
            if "model_version" not in metadata:
                raise ValueError(
                    "PREDICT actions must include 'model_version' in metadata "
                    "(Requirement 14.5)"
                )
        
        # Create audit log entry (Requirement 14.4)
        audit_log = AuditLog(
            student_id=student_id,
            prediction_id=prediction_id,
            action=action,
            performed_by=performed_by,
            action_metadata=metadata or {}
        )
        
        # Add to session and flush to get ID
        # Timestamp is automatically set by database (Requirement 14.6)
        db.add(audit_log)
        await db.flush()
        await db.refresh(audit_log)
        
        return audit_log
    
    @staticmethod
    async def log_predict(
        db: AsyncSession,
        student_id: UUID,
        prediction_id: UUID,
        model_version: str,
        risk_level: str,
        risk_score: int,
        alert_triggered: bool,
        performed_by: Optional[str] = "system"
    ) -> AuditLog:
        """
        Convenience method to log a PREDICT action.
        
        This method provides a type-safe interface for logging prediction
        actions with all required metadata fields.
        
        Args:
            db: Async database session
            student_id: UUID of the student record
            prediction_id: UUID of the prediction record
            model_version: ML model version string (required by Requirement 14.5)
            risk_level: Assigned risk level (low/medium/high)
            risk_score: Computed risk score (0-100)
            alert_triggered: Whether high-risk alert was triggered
            performed_by: User or system identifier (default: "system")
            
        Returns:
            Created AuditLog ORM object
            
        Requirements:
            - 14.1: Log PREDICT action
            - 14.5: Include model_version in metadata
        """
        metadata = {
            "model_version": model_version,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "alert_triggered": alert_triggered
        }
        
        return await AuditLogger.log_action(
            db=db,
            action="PREDICT",
            student_id=student_id,
            prediction_id=prediction_id,
            performed_by=performed_by,
            metadata=metadata
        )
    
    @staticmethod
    async def log_explain(
        db: AsyncSession,
        student_id: UUID,
        prediction_id: UUID,
        performed_by: Optional[str] = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Convenience method to log an EXPLAIN action.
        
        This method provides a type-safe interface for logging explanation
        retrieval actions.
        
        Args:
            db: Async database session
            student_id: UUID of the student record
            prediction_id: UUID of the prediction record
            performed_by: User or system identifier (default: "system")
            metadata: Optional additional metadata
            
        Returns:
            Created AuditLog ORM object
            
        Requirements:
            - 14.2: Log EXPLAIN action when SHAP explanation is retrieved
        """
        return await AuditLogger.log_action(
            db=db,
            action="EXPLAIN",
            student_id=student_id,
            prediction_id=prediction_id,
            performed_by=performed_by,
            metadata=metadata or {}
        )
    
    @staticmethod
    async def log_alert_sent(
        db: AsyncSession,
        student_id: UUID,
        prediction_id: UUID,
        alert_type: str,
        risk_score: int,
        performed_by: Optional[str] = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Convenience method to log an ALERT_SENT action.
        
        This method provides a type-safe interface for logging high-risk
        alert actions.
        
        Args:
            db: Async database session
            student_id: UUID of the student record
            prediction_id: UUID of the prediction record
            alert_type: Type of alert (e.g., "high_risk", "emi_stress")
            risk_score: Computed risk score (0-100)
            performed_by: User or system identifier (default: "system")
            metadata: Optional additional metadata
            
        Returns:
            Created AuditLog ORM object
            
        Requirements:
            - 14.3: Log ALERT_SENT action when high-risk alert is triggered
        """
        alert_metadata = {
            "alert_type": alert_type,
            "risk_score": risk_score
        }
        
        # Merge with additional metadata if provided
        if metadata:
            alert_metadata.update(metadata)
        
        return await AuditLogger.log_action(
            db=db,
            action="ALERT_SENT",
            student_id=student_id,
            prediction_id=prediction_id,
            performed_by=performed_by,
            metadata=alert_metadata
        )
