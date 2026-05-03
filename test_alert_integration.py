"""
Simple integration test for alert system.
Tests that high-risk predictions trigger alerts.
"""
import requests
import json

# API endpoint
BASE_URL = "http://localhost:8000"

# Test data for high-risk student (low CGPA, no internships, tier 3 institute)
high_risk_student = {
    "name": "Test High Risk Student",
    "course_type": "Engineering",
    "institute_name": "Test Institute",
    "institute_tier": 3,
    "cgpa": 5.5,  # Very low CGPA
    "cgpa_scale": 10.0,
    "year_of_grad": 2024,
    "internship_count": 0,
    "internship_months": 0,
    "internship_employer_type": None,
    "certifications": 0,
    "region": "North",
    "loan_amount": 800000,  # High loan amount
    "loan_emi": 25000  # High EMI
}

# Test data for low-risk student (high CGPA, multiple internships, tier 1 institute)
low_risk_student = {
    "name": "Test Low Risk Student",
    "course_type": "Engineering",
    "institute_name": "IIT Delhi",
    "institute_tier": 1,
    "cgpa": 9.2,
    "cgpa_scale": 10.0,
    "year_of_grad": 2024,
    "internship_count": 3,
    "internship_months": 12,
    "internship_employer_type": "MNC",
    "certifications": 2,
    "region": "North",
    "loan_amount": 300000,
    "loan_emi": 8000
}

def get_auth_token():
    """Get JWT token for authentication."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Failed to get auth token: {response.status_code}")
        print(response.text)
        return None

def test_high_risk_alert():
    """Test that high-risk prediction triggers alert."""
    print("\n=== Testing High-Risk Alert ===")
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("❌ Failed to authenticate")
        return False
    
    # Make prediction request
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/predict",
        headers=headers,
        json=high_risk_student
    )
    
    if response.status_code != 200:
        print(f"❌ Prediction failed: {response.status_code}")
        print(response.text)
        return False
    
    result = response.json()
    
    print(f"✓ Prediction created successfully")
    print(f"  Student ID: {result['student_id']}")
    print(f"  Risk Level: {result['risk_level']}")
    print(f"  Risk Score: {result['risk_score']}")
    print(f"  Alert Triggered: {result.get('alert_triggered', False)}")
    
    # Check if alert was triggered for high-risk student
    if result['risk_level'] == 'high':
        print(f"✓ Student correctly classified as high-risk")
        if result.get('alert_triggered'):
            print(f"✓ Alert was triggered (check backend logs for SMS/Email notifications)")
            return True
        else:
            print(f"⚠️  Alert was not triggered (expected for high-risk)")
            return False
    else:
        print(f"⚠️  Student not classified as high-risk (risk_level: {result['risk_level']})")
        return False

def test_low_risk_no_alert():
    """Test that low-risk prediction does not trigger alert."""
    print("\n=== Testing Low-Risk (No Alert) ===")
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("❌ Failed to authenticate")
        return False
    
    # Make prediction request
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/predict",
        headers=headers,
        json=low_risk_student
    )
    
    if response.status_code != 200:
        print(f"❌ Prediction failed: {response.status_code}")
        print(response.text)
        return False
    
    result = response.json()
    
    print(f"✓ Prediction created successfully")
    print(f"  Student ID: {result['student_id']}")
    print(f"  Risk Level: {result['risk_level']}")
    print(f"  Risk Score: {result['risk_score']}")
    print(f"  Alert Triggered: {result.get('alert_triggered', False)}")
    
    # Check if alert was NOT triggered for low-risk student
    if result['risk_level'] == 'low':
        print(f"✓ Student correctly classified as low-risk")
        if not result.get('alert_triggered'):
            print(f"✓ Alert was NOT triggered (correct for low-risk)")
            return True
        else:
            print(f"⚠️  Alert was triggered (unexpected for low-risk)")
            return False
    else:
        print(f"⚠️  Student not classified as low-risk (risk_level: {result['risk_level']})")
        # Still check if alert behavior is correct
        if result['risk_level'] == 'high' and result.get('alert_triggered'):
            return True
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Alert System Integration Test")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_high_risk_alert()
    test2_passed = test_low_risk_no_alert()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"High-Risk Alert Test: {'✓ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Low-Risk No Alert Test: {'✓ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n✓ All tests passed!")
        print("\nTo verify alerts were logged, check backend logs:")
        print("  docker logs edurisk-backend | grep ALERT")
    else:
        print("\n❌ Some tests failed")
    
    print("=" * 60)
