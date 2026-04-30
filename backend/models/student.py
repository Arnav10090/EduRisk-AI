"""
Student ORM model.

Represents student academic, internship, and loan information.
"""

from sqlalchemy import Column, String, Integer, Numeric, CheckConstraint, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..db.session import Base


class Student(Base):
    """
    Student model representing academic and loan information.
    
    Stores student profile data including academic performance, internship experience,
    and loan details for placement risk assessment.
    """
    
    __tablename__ = "students"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Unique student identifier"
    )
    
    # Basic information
    name = Column(
        String(255),
        nullable=False,
        comment="Student full name"
    )
    
    # Academic information
    course_type = Column(
        String(100),
        nullable=False,
        comment="Course type (e.g., Engineering, MBA, etc.)"
    )
    
    institute_name = Column(
        String(255),
        nullable=True,
        comment="Name of the educational institute"
    )
    
    institute_tier = Column(
        Integer,
        nullable=False,
        comment="Institute tier classification (1-3, where 1 is highest)"
    )
    
    cgpa = Column(
        Numeric(4, 2),
        nullable=True,
        comment="Cumulative Grade Point Average"
    )
    
    cgpa_scale = Column(
        Numeric(4, 2),
        nullable=False,
        default=10.0,
        server_default="10.0",
        comment="CGPA scale (typically 4.0 or 10.0)"
    )
    
    year_of_grad = Column(
        Integer,
        nullable=False,
        comment="Year of graduation"
    )
    
    # Internship information
    internship_count = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of internships completed"
    )
    
    internship_months = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Total months of internship experience"
    )
    
    internship_employer_type = Column(
        String(100),
        nullable=True,
        comment="Type of internship employer (MNC, Startup, PSU, NGO, etc.)"
    )
    
    certifications = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of professional certifications"
    )
    
    # Location information
    region = Column(
        String(100),
        nullable=True,
        comment="Geographic region (North, South, East, West, etc.)"
    )
    
    # Loan information
    loan_amount = Column(
        Numeric(12, 2),
        nullable=True,
        comment="Total loan amount in INR"
    )
    
    loan_emi = Column(
        Numeric(10, 2),
        nullable=True,
        comment="Monthly EMI amount in INR"
    )
    
    # Timestamps
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp"
    )
    
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Record last update timestamp"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "institute_tier >= 1 AND institute_tier <= 3",
            name="check_institute_tier_range"
        ),
        CheckConstraint(
            "cgpa >= 0",
            name="check_cgpa_non_negative"
        ),
        CheckConstraint(
            "cgpa <= cgpa_scale",
            name="check_cgpa_within_scale"
        ),
        CheckConstraint(
            "year_of_grad >= 2020 AND year_of_grad <= 2030",
            name="check_year_of_grad_range"
        ),
        CheckConstraint(
            "internship_count >= 0",
            name="check_internship_count_non_negative"
        ),
        CheckConstraint(
            "internship_months >= 0",
            name="check_internship_months_non_negative"
        ),
        CheckConstraint(
            "certifications >= 0",
            name="check_certifications_non_negative"
        ),
        CheckConstraint(
            "loan_amount >= 0",
            name="check_loan_amount_non_negative"
        ),
        CheckConstraint(
            "loan_emi >= 0",
            name="check_loan_emi_non_negative"
        ),
    )
    
    # Relationships
    predictions = relationship(
        "Prediction",
        back_populates="student",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    audit_logs = relationship(
        "AuditLog",
        back_populates="student",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return (
            f"<Student(id={self.id}, name='{self.name}', "
            f"course_type='{self.course_type}', tier={self.institute_tier})>"
        )
