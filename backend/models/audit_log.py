"""
AuditLog ORM model.

Represents audit trail for compliance tracking of all predictions and actions.
"""

from sqlalchemy import Column, String, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..db.session import Base


class AuditLog(Base):
    """
    AuditLog model for compliance tracking.
    
    Maintains an append-only audit trail of all predictions, explanations,
    and alerts for RBI regulatory compliance. Records are never deleted.
    """
    
    __tablename__ = "audit_logs"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Unique audit log identifier"
    )
    
    # Foreign keys (SET NULL on delete to preserve audit trail)
    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Reference to student record (nullable for audit preservation)"
    )
    
    prediction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("predictions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Reference to prediction record (nullable for audit preservation)"
    )
    
    # Action information
    action = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Action type (PREDICT, EXPLAIN, ALERT_SENT, etc.)"
    )
    
    performed_by = Column(
        String(100),
        nullable=True,
        comment="User or system identifier that performed the action"
    )
    
    # Metadata (JSONB for flexible schema)
    # Note: Using 'action_metadata' instead of 'metadata' to avoid SQLAlchemy reserved name
    action_metadata = Column(
        'metadata',  # Database column name
        JSONB,
        nullable=True,
        comment="Additional action metadata (model_version, processing_time, etc.)"
    )
    
    # Timestamp
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Action timestamp"
    )
    
    # Relationships
    student = relationship(
        "Student",
        back_populates="audit_logs"
    )
    
    prediction = relationship(
        "Prediction",
        back_populates="audit_logs"
    )
    
    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, action='{self.action}', "
            f"student_id={self.student_id}, created_at={self.created_at})>"
        )
