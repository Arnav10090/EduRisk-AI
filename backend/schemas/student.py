"""
Student request schemas for API validation.

Implements Pydantic v2 schemas for student data input and batch scoring requests.
"""

from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, ConfigDict


class StudentInput(BaseModel):
    """
    Schema for student profile input data.
    
    Validates all student fields according to business rules:
    - Institute tier must be between 1-3
    - CGPA must be <= cgpa_scale
    - Year of graduation must be between 2020-2030
    - All count/amount fields must be non-negative
    
    Validates Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        json_schema_extra={
            "example": {
                "name": "Rahul Sharma",
                "course_type": "Engineering",
                "institute_name": "IIT Delhi",
                "institute_tier": 1,
                "cgpa": 8.5,
                "cgpa_scale": 10.0,
                "year_of_grad": 2025,
                "internship_count": 2,
                "internship_months": 6,
                "internship_employer_type": "MNC",
                "certifications": 3,
                "region": "North",
                "loan_amount": 500000.00,
                "loan_emi": 15000.00
            }
        }
    )
    
    # Basic information
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Student full name"
    )
    
    # Academic information
    course_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Course type (e.g., Engineering, MBA, etc.)"
    )
    
    institute_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Name of the educational institute"
    )
    
    institute_tier: int = Field(
        ...,
        ge=1,
        le=3,
        description="Institute tier classification (1-3, where 1 is highest)"
    )
    
    cgpa: Optional[Decimal] = Field(
        None,
        ge=0,
        decimal_places=2,
        description="Cumulative Grade Point Average"
    )
    
    cgpa_scale: Decimal = Field(
        default=Decimal("10.0"),
        gt=0,
        decimal_places=2,
        description="CGPA scale (typically 4.0 or 10.0)"
    )
    
    year_of_grad: int = Field(
        ...,
        ge=2020,
        le=2030,
        description="Year of graduation (must be between 2020 and 2030)"
    )
    
    # Internship information
    internship_count: int = Field(
        default=0,
        ge=0,
        description="Number of internships completed (must be non-negative)"
    )
    
    internship_months: int = Field(
        default=0,
        ge=0,
        description="Total months of internship experience (must be non-negative)"
    )
    
    internship_employer_type: Optional[str] = Field(
        None,
        max_length=100,
        description="Type of internship employer (MNC, Startup, PSU, NGO, etc.)"
    )
    
    certifications: int = Field(
        default=0,
        ge=0,
        description="Number of professional certifications (must be non-negative)"
    )
    
    # Location information
    region: Optional[str] = Field(
        None,
        max_length=100,
        description="Geographic region (North, South, East, West, etc.)"
    )
    
    # Loan information
    loan_amount: Optional[Decimal] = Field(
        None,
        ge=0,
        decimal_places=2,
        description="Total loan amount in INR (must be non-negative)"
    )
    
    loan_emi: Optional[Decimal] = Field(
        None,
        ge=0,
        decimal_places=2,
        description="Monthly EMI amount in INR (must be non-negative)"
    )
    
    @field_validator("cgpa")
    @classmethod
    def validate_cgpa_within_scale(cls, v: Optional[Decimal], info) -> Optional[Decimal]:
        """
        Validate that CGPA does not exceed the CGPA scale.
        
        Validates Requirement: 20.3
        """
        if v is None:
            return v
        
        # Get cgpa_scale from the data being validated
        cgpa_scale = info.data.get("cgpa_scale", Decimal("10.0"))
        
        if v > cgpa_scale:
            raise ValueError(
                f"CGPA ({v}) cannot exceed CGPA scale ({cgpa_scale})"
            )
        
        return v
    
    @field_validator("institute_tier")
    @classmethod
    def validate_institute_tier(cls, v: int) -> int:
        """
        Validate that institute tier is between 1 and 3.
        
        Validates Requirement: 20.2
        """
        if not (1 <= v <= 3):
            raise ValueError(
                f"Institute tier must be between 1 and 3, got {v}"
            )
        return v
    
    @field_validator("year_of_grad")
    @classmethod
    def validate_year_of_grad(cls, v: int) -> int:
        """
        Validate that year of graduation is between 2020 and 2030.
        
        Validates Requirement: 20.4
        """
        if not (2020 <= v <= 2030):
            raise ValueError(
                f"Year of graduation must be between 2020 and 2030, got {v}"
            )
        return v


class BatchScoreRequest(BaseModel):
    """
    Schema for batch scoring request accepting multiple student profiles.
    
    Validates Requirements: 20.5, 20.6
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "students": [
                    {
                        "name": "Rahul Sharma",
                        "course_type": "Engineering",
                        "institute_tier": 1,
                        "cgpa": 8.5,
                        "cgpa_scale": 10.0,
                        "year_of_grad": 2025
                    },
                    {
                        "name": "Priya Patel",
                        "course_type": "MBA",
                        "institute_tier": 2,
                        "cgpa": 7.8,
                        "cgpa_scale": 10.0,
                        "year_of_grad": 2024
                    }
                ]
            }
        }
    )
    
    students: List[StudentInput] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Array of student profiles to score (maximum 500)"
    )
    
    @field_validator("students")
    @classmethod
    def validate_batch_size(cls, v: List[StudentInput]) -> List[StudentInput]:
        """
        Validate that batch size does not exceed 500 students.
        
        Validates Requirement: 9.2
        """
        if len(v) > 500:
            raise ValueError(
                f"Batch size cannot exceed 500 students, got {len(v)}"
            )
        if len(v) == 0:
            raise ValueError(
                "Batch must contain at least one student"
            )
        return v
