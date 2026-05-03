"""
Manual test script for async SHAP computation.

This script demonstrates the async SHAP computation feature by:
1. Submitting a batch of students
2. Verifying the response is fast (< 5 seconds)
3. Polling for SHAP values
4. Verifying SHAP values are eventually available

Run this script with the backend server running:
    python backend/tests/manual_test_async_shap.py
"""

import requests
import time
import json
from typing import List, Dict


# Configuration
BASE_URL = "http://localhost:8000/api"
API_KEY = "your_api_key_here"  # Replace with actual API key
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}


def create_test_student(name: str) -> Dict:
    """Create a test student profile."""
    return {
        "name": name,
        "course_type": "Engineering",
        "institute_name": "Test Institute",
        "institute_tier": 1,
        "cgpa": 8.5,
        "cgpa_scale": 10.0,
        "year_of_grad": 2024,
        "internship_count": 2,
        "internship_months": 6,
        "internship_employer_type": "startup",
        "certifications": ["AWS", "Python"],
        "region": "metro",
        "loan_amount": 500000,
        "loan_emi": 10000
    }


def test_batch_scoring_speed():
    """Test that batch scoring returns quickly without SHAP values."""
    print("\n" + "="*80)
    print("TEST 1: Batch Scoring Speed (Requirement 27.2, 27.5)")
    print("="*80)
    
    # Create batch of 10 students
    students = [create_test_student(f"Student {i}") for i in range(10)]
    
    print(f"Submitting batch of {len(students)} students...")
    start_time = time.time()
    
    response = requests.post(
        f"{BASE_URL}/batch-score",
        headers=HEADERS,
        json={"students": students}
    )
    
    elapsed_time = time.time() - start_time
    
    print(f"Response status: {response.status_code}")
    print(f"Response time: {elapsed_time:.2f} seconds")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Batch scoring successful!")
        print(f"   - Total students: {len(data['results'])}")
        print(f"   - Summary: {data['summary']}")
        
        if elapsed_time < 5.0:
            print(f"✅ Response time < 5 seconds (Requirement 27.5 met)")
        else:
            print(f"❌ Response time >= 5 seconds (Requirement 27.5 NOT met)")
        
        return data['results']
    else:
        print(f"❌ Batch scoring failed: {response.text}")
        return []


def test_empty_shap_values(results: List[Dict]):
    """Test that initial response has empty SHAP values."""
    print("\n" + "="*80)
    print("TEST 2: Empty SHAP Values in Initial Response (Requirement 27.3)")
    print("="*80)
    
    if not results:
        print("❌ No results to test")
        return
    
    first_result = results[0]
    print(f"Checking first result (prediction_id: {first_result['prediction_id']})")
    
    if 'top_risk_drivers' in first_result:
        if len(first_result['top_risk_drivers']) == 0:
            print("✅ top_risk_drivers is empty (Requirement 27.3 met)")
        else:
            print(f"❌ top_risk_drivers is NOT empty: {first_result['top_risk_drivers']}")
    else:
        print("❌ top_risk_drivers field missing")


def test_shap_retrieval(prediction_id: str):
    """Test SHAP retrieval endpoint."""
    print("\n" + "="*80)
    print("TEST 3: SHAP Retrieval Endpoint (Requirement 27.4)")
    print("="*80)
    
    print(f"Polling for SHAP values (prediction_id: {prediction_id})")
    
    max_attempts = 15
    wait_interval = 2
    
    for attempt in range(1, max_attempts + 1):
        print(f"Attempt {attempt}/{max_attempts}...", end=" ")
        
        response = requests.get(
            f"{BASE_URL}/predictions/{prediction_id}/shap",
            headers=HEADERS
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SHAP values available!")
            print(f"   - Student ID: {data['student_id']}")
            print(f"   - Base value: {data['base_value']}")
            print(f"   - Prediction: {data['prediction']}")
            print(f"   - SHAP values count: {len(data['shap_values'])}")
            print(f"   - Waterfall data points: {len(data['waterfall_data'])}")
            
            # Show top 3 SHAP values
            sorted_shap = sorted(
                data['shap_values'].items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )[:3]
            print(f"   - Top 3 features:")
            for feature, value in sorted_shap:
                print(f"     * {feature}: {value:.4f}")
            
            print(f"✅ Requirement 27.4.2 met (SHAP values returned)")
            return True
            
        elif response.status_code == 404:
            if "still being computed" in response.json().get('detail', '').lower():
                print(f"⏳ Still computing...")
                if attempt == 1:
                    print(f"✅ Requirement 27.4.3 met (404 when not ready)")
            else:
                print(f"❌ Prediction not found")
                return False
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            return False
        
        if attempt < max_attempts:
            time.sleep(wait_interval)
    
    print(f"❌ SHAP values not available after {max_attempts * wait_interval} seconds")
    return False


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("ASYNC SHAP COMPUTATION MANUAL TEST")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {'*' * len(API_KEY)}")
    
    # Test 1: Batch scoring speed
    results = test_batch_scoring_speed()
    
    if not results:
        print("\n❌ Cannot continue tests without successful batch scoring")
        return
    
    # Test 2: Empty SHAP values
    test_empty_shap_values(results)
    
    # Test 3: SHAP retrieval
    prediction_id = results[0]['prediction_id']
    test_shap_retrieval(prediction_id)
    
    print("\n" + "="*80)
    print("TESTS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend server")
        print("   Make sure the backend is running: docker-compose up backend")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
