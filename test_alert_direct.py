"""
Direct test of alert service functionality.
Creates a mock high-risk prediction and verifies alert is triggered.
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.alert_service import AlertService
from backend.models.student import Student
from backend.models.prediction import Prediction
from uuid import uuid4
from unittest.mock import AsyncMock

async def test_alert_service():
    """Test alert service with mock high-risk prediction."""
    print("=" * 60)
    print("Direct Alert Service Test")
    print("=" * 60)
    
    # Create alert service
    alert_service = AlertService()
    
    print(f"\nAlert Service Configuration:")
    print(f"  Enabled: {alert_service.alert_enabled}")
    print(f"  Phone: {alert_service.alert_phone}")
    print(f"  Email: {alert_service.alert_email}")
    
    # Create mock student
    student = Student(
        id=uuid4(),
        name="Test High Risk Student",
        course_type="Engineering",
        institute_tier=3,
        cgpa=5.5,
        cgpa_scale=10.0,
        year_of_grad=2024,
        internship_count=0,
        internship_months=0,
        certifications=0
    )
    
    # Create mock high-risk prediction
    prediction = Prediction(
        id=uuid4(),
        student_id=student.id,
        risk_score=85,  # High risk score
        risk_level="high",
        prob_placed_3m=0.2,
        prob_placed_6m=0.4,
        prob_placed_12m=0.6,
        placement_label="high_risk",
        salary_min=350000,
        salary_max=450000,
        salary_confidence=0.75,
        model_version="1.0.0",
        shap_values={},
        top_risk_drivers=[],
        next_best_actions=["Improve technical skills", "Apply to more companies", "Consider skill development courses"],
        alert_triggered=False
    )
    
    print(f"\nTest Student:")
    print(f"  Name: {student.name}")
    print(f"  Risk Score: {prediction.risk_score}")
    print(f"  Risk Level: {prediction.risk_level}")
    
    # Mock database session
    mock_db = AsyncMock()
    
    print(f"\nSending alert...")
    print("-" * 60)
    
    # Send alert
    result = await alert_service.send_high_risk_alert(
        student=student,
        prediction=prediction,
        db=mock_db,
        performed_by="test_user"
    )
    
    print("-" * 60)
    print(f"\nAlert Result: {'✓ SENT' if result else '❌ NOT SENT'}")
    
    if result:
        print(f"\n✓ Alert service is working correctly!")
        print(f"  - SMS notification logged")
        print(f"  - Email notification logged")
        print(f"  - Audit log entry created")
        print(f"\nCheck the output above for:")
        print(f"  📱 ALERT: SMS sent to {alert_service.alert_phone}")
        print(f"  📧 ALERT: Email sent to {alert_service.alert_email}")
    else:
        print(f"\n❌ Alert was not sent")
        print(f"  This could be because:")
        print(f"  - ALERT_ENABLED is set to false")
        print(f"  - Risk score < 67")
    
    print("=" * 60)
    
    # Test with medium risk (should not trigger)
    print(f"\nTesting with medium-risk student (should NOT trigger alert)...")
    print("-" * 60)
    
    prediction.risk_score = 50
    prediction.risk_level = "medium"
    
    result2 = await alert_service.send_high_risk_alert(
        student=student,
        prediction=prediction,
        db=mock_db,
        performed_by="test_user"
    )
    
    print("-" * 60)
    print(f"\nAlert Result: {'✓ SENT' if result2 else '✓ NOT SENT (correct)'}")
    
    if not result2:
        print(f"\n✓ Alert service correctly skipped medium-risk student")
    else:
        print(f"\n❌ Alert was sent for medium-risk student (unexpected)")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_alert_service())
